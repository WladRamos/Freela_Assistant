from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db import IntegrityError
from Assistant_app.services.router import get_router_decision
from Assistant_app.services.ClassJobFetch import JobFetcher
from Assistant_app.services.llmSearchJobs import get_llm_response_search
from Assistant_app.services.llmAnalyzeJob import get_llm_response_analyze
from Assistant_app.services.llmTips import answer_user_question
from Assistant_app.services.llmOther import get_llm_response_other
from Assistant_app.services.llmChatTitle import generate_chat_title
from Assistant_app.services.llmFilterMaker import get_user_info, generate_filter
import json
from django.contrib.auth import authenticate, login, logout
from .models import User, ProjetoHistorico, UsuarioHabilidade, Habilidade, ProjetoHabilidade, Chat, Mensagem, RespostaAssistente, TipoUsuario, Banimento, Suspensao
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib import messages
from django.utils.timezone import now
from pathlib import Path
import chromadb

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verifica se o usuário está banido
            if hasattr(user, 'banimento'):
                return render(request, "assistant/login.html", {
                    "message": f"Conta banida. Motivo: {user.banimento.justificativa}"
                })

            # Verifica se há alguma suspensão ativa
            suspensoes_ativas = user.suspensoes.filter(data_inicio__lte=now())
            suspensoes_ativas = [s for s in suspensoes_ativas if s.ativa]

            if suspensoes_ativas:
                s = suspensoes_ativas[-1]  # pega a mais recente
                return render(request, "assistant/login.html", {
                    "message": f"Conta suspensa até {s.data_fim.strftime('%d/%m/%Y %H:%M')}. Motivo: {s.justificativa}"
                })

            # Se passou por todas as verificações
            login(request, user)
            return HttpResponseRedirect(reverse("index"))

        else:
            return render(request, "assistant/login.html", {
                "message": "Usuário e/ou senha inválidos."
            })
    else:
        return render(request, "assistant/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"].strip()
        email = request.POST["email"].strip()

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "assistant/register.html", {
                "message": "Passwords must match."
            })

        # Verifica se o username ou email estão banidos
        if Banimento.objects.filter(username_backup=username).exists():
            return render(request, "assistant/register.html", {
                "message": "Este nome de usuário está banido."
            })

        if Banimento.objects.filter(email_backup=email).exists():
            return render(request, "assistant/register.html", {
                "message": "Este email está banido."
            })

        # Tenta criar o usuário
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "assistant/register.html", {
                "message": "Nome de usuário já está em uso."
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))

    else:
        return render(request, "assistant/register.html")

@login_required
def index(request):
    if request.user.tipo_usuario == TipoUsuario.ADMINISTRADOR:
        return render(request, "assistant/admin-area.html")
    return render(request, "assistant/index.html")

def profile(request):
    return render(request, "assistant/profile.html")

def gerar_contexto_conversa(chat, limite_mensagens=5):
    mensagens = chat.mensagens.order_by("data").prefetch_related("resposta_assistente")[:limite_mensagens]
    contexto = "Contexto da conversa: \n"
    for m in mensagens:
        contexto += f"Usuário: {m.conteudo.strip()}\n"
        if hasattr(m, "resposta_assistente"):
            contexto += f"Assistente: {m.resposta_assistente.conteudo.strip()}\n"
    return contexto.strip()
    
def chat_llm(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get('message')
        chat_id = data.get('chat_id')

        if not request.user.is_authenticated:
            return JsonResponse({"error": "Usuário não autenticado"}, status=403)

        # Criar um novo chat se necessário
        if not chat_id:
            titulo_chat = generate_chat_title(user_message)
            if titulo_chat:
                chat = Chat.objects.create(usuario=request.user, nome=titulo_chat)
            else:
                chat = Chat.objects.create(usuario=request.user)
            contexto = ""
        else:
            chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)
            contexto = gerar_contexto_conversa(chat)

        mensagem = Mensagem.objects.create(chat=chat, conteudo=user_message)

        router_decision = get_router_decision(user_message)
        
        user_info = get_user_info(request.user.id)

        response = None

        if router_decision == "search_jobs":
            filters = generate_filter(user_message, user_info)
            jobs = JobFetcher(filters)
            jobs_str = jobs.get_jobs_str()
            response = get_llm_response_search(user_message, jobs_str, user_info, contexto) if jobs_str else 'Não foi possível encontrar trabalhos no momento.'
        elif router_decision == "analyze_job":
            response = get_llm_response_analyze(user_message, user_info, contexto) or 'Não foi possível analisar o trabalho no momento.'
        elif router_decision == "freelancing_tips":
            response = answer_user_question(user_message, user_info, contexto) or 'Não foi possível encontrar dicas no momento.'
        else:
            response = get_llm_response_other(user_message, user_info, contexto)

        if not response:   
            response = "Desculpe, houve um erro ao processar a sua solicitação."

        RespostaAssistente.objects.create(mensagem=mensagem, conteudo=response)

        return JsonResponse({"response": response, "chat_id": chat.id})
    else:
        return JsonResponse({"error": "Método inválido."}, status=405)
    

#Salvar ou Editar Trabalho
@login_required
def salvar_trabalho(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

    try:
        data = json.loads(request.body)
        user = request.user

        # Se o ID existir, atualiza o trabalho existente
        if data.get("id"):
            projeto = get_object_or_404(ProjetoHistorico, id=data["id"], usuario=user)
            projeto.titulo = data["titulo"]
            projeto.descricao = data["descricao"]
            projeto.tipo_pagamento = data["tipo_pagamento"]
            projeto.valor_pagamento = data["valor_pagamento"]
            projeto.save()

            #Remover habilidades antigas associadas ao projeto
            ProjetoHabilidade.objects.filter(projeto=projeto).delete()
        else:
            # Criar um novo trabalho
            projeto = ProjetoHistorico.objects.create(
                usuario=user,
                titulo=data["titulo"],
                descricao=data["descricao"],
                tipo_pagamento=data["tipo_pagamento"],
                valor_pagamento=data["valor_pagamento"]
            )

        #Adicionar habilidades ao trabalho
        for habilidade_data in data.get("habilidades", []):
            nome_habilidade = habilidade_data.get("nome").strip()

            if nome_habilidade:
                # Normaliza o nome da habilidade (por exemplo, tudo em maiúsculas)
                habilidade, created = Habilidade.objects.get_or_create(nome=nome_habilidade.upper())

                # Criar a relação entre o trabalho e a habilidade
                ProjetoHabilidade.objects.create(projeto=projeto, habilidade=habilidade)

        return JsonResponse({"success": True, "id": projeto.id})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


#Excluir Trabalho
@login_required
def excluir_trabalho(request, trabalho_id):
    if request.method != "DELETE":
        return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

    try:
        user = request.user
        projeto = get_object_or_404(ProjetoHistorico, id=trabalho_id, usuario=user)
        projeto.delete()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


#Salvar Preferências de Preços
@login_required
def salvar_precos(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

    try:
        data = json.loads(request.body)
        user = request.user

        user.preco_fixo_min = float(data.get("preco_fixo_min", user.preco_fixo_min))
        user.preco_hora_min = float(data.get("preco_hora_min", user.preco_hora_min))
        user.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


#Adicionar Habilidade
@login_required
def adicionar_habilidade(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

    try:
        data = json.loads(request.body)
        user = request.user

        skill_name = Habilidade.normalizar_nome(data["nome"])
        habilidade, _ = Habilidade.objects.get_or_create(nome=skill_name)
        UsuarioHabilidade.objects.get_or_create(usuario=user, habilidade=habilidade)

        return JsonResponse({"success": True, "habilidade_id": habilidade.id})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


#Remover Habilidade
@login_required
def remover_habilidade(request, habilidade_id):
    if request.method != "DELETE":
        return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

    try:
        user = request.user
        habilidade = get_object_or_404(Habilidade, id=habilidade_id)
        UsuarioHabilidade.objects.filter(usuario=user, habilidade=habilidade).delete()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

@login_required
def get_trabalho(request, trabalho_id):
    try:
        trabalho = ProjetoHistorico.objects.get(id=trabalho_id, usuario=request.user)
        habilidades = ProjetoHabilidade.objects.filter(projeto=trabalho).select_related("habilidade")

        return JsonResponse({
            "id": trabalho.id,
            "titulo": trabalho.titulo,
            "descricao": trabalho.descricao,
            "tipo_pagamento": trabalho.tipo_pagamento,
            "valor_pagamento": trabalho.valor_pagamento,
            "habilidades": [{"id": h.habilidade.id, "nome": h.habilidade.nome} for h in habilidades]
        })
    except ProjetoHistorico.DoesNotExist:
        return JsonResponse({"error": "Trabalho não encontrado"}, status=404)

@login_required    
def chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)
    return render(request, "assistant/index.html", {"chat_id": chat.id})

@login_required
def get_chat_messages(request, chat_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Usuário não autenticado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, usuario=request.user)
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat não encontrado"}, status=404)

    mensagens = chat.mensagens.order_by("data").values("id", "conteudo", "data")
    respostas = {r.mensagem.id: {"id": r.id, "conteudo": r.conteudo, "data": r.data.strftime("%d/%m/%Y %H:%M")} for r in RespostaAssistente.objects.filter(mensagem__chat=chat)}

    mensagens_lista = []
    for msg in mensagens:
        mensagens_lista.append({
            "id": msg["id"],
            "conteudo": msg["conteudo"],
            "data": msg["data"].strftime("%d/%m/%Y %H:%M"),
            "resposta": respostas.get(msg["id"])
        })

    return JsonResponse({"mensagens": mensagens_lista})

@login_required
def get_chats(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Usuário não autenticado"}, status=403)

    chats = Chat.objects.filter(usuario=request.user).order_by("-data")
    chat_list = [{"id": chat.id, "nome": chat.nome, "data": chat.data.strftime("%d/%m/%Y %H:%M")} for chat in chats]

    return JsonResponse({"chats": chat_list})

# View para renomear um chat
@login_required
def rename_chat(request, chat_id):
    if request.method == "POST":
        data = json.loads(request.body)
        new_name = data.get("nome", "").strip()

        if not new_name:
            return JsonResponse({"error": "Nome inválido."}, status=400)

        chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)
        chat.nome = new_name
        chat.save(update_fields=["nome"])

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método não permitido."}, status=405)

# View para excluir um chat
@login_required
def delete_chat(request, chat_id):
    if request.method == "DELETE":
        chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)
        chat.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método não permitido."}, status=405)


@login_required
def admin_user_list(request):
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'mensagens')

    users = User.objects.filter(tipo_usuario=TipoUsuario.USUARIO).annotate(
        num_chats=Count('chats', distinct=True),
        num_mensagens=Count('chats__mensagens', distinct=True)
    )

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if sort_by == 'chats':
        users = users.order_by('-num_chats')
    else:
        users = users.order_by('-num_mensagens')

    paginator = Paginator(users, 10)  # 10 usuários por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'assistant/admin-users.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    })

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'Administrador')
def ban_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        justificativa = request.POST.get('justificativa')
        user = get_object_or_404(User, id=user_id)

        # Registra o banimento
        Banimento.objects.create(
            usuario=user,
            justificativa=justificativa,
            username_backup=user.username,
            email_backup=user.email,
            data=now()
        )

        # Exclui o usuário
        user.delete()

        messages.success(request, f'Usuário banido e removido do sistema com sucesso.')
    return redirect('admin_user_list')

@user_passes_test(lambda u: u.tipo_usuario == 'Administrador')
def suspend_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        justificativa = request.POST.get('justificativa')
        dias = int(request.POST.get('dias') or 0)
        horas = int(request.POST.get('horas') or 0)
        user = get_object_or_404(User, id=user_id)

        # Cria uma suspensão
        Suspensao.objects.create(
            usuario=user,
            justificativa=justificativa,
            data_inicio=now(),
            duracao_dias=dias,
            duracao_horas=horas
        )

        messages.success(request, f'Usuário suspenso por {dias} dias e {horas} horas.')
    return redirect('admin_user_list')

@user_passes_test(lambda u: u.tipo_usuario == 'Administrador')
def admin_vector_base(request):
    base_dir = Path(__file__).resolve().parent
    caminho_persistent_client = base_dir.parent

    client = chromadb.PersistentClient(path=str(caminho_persistent_client))

    try:
        collection = client.get_collection("Base_de_Trabalhos")
        all_ids = collection.get(include=[])["ids"]
    except Exception as e:
        return render(request, "assistant/admin-vector-error.html", {
            "message": f"Erro ao acessar a base vetorial: {str(e)}"
        })

    # Paginação com base apenas nos IDs
    paginator = Paginator(all_ids, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    try:
        # Buscar apenas os documentos da página atual
        resultados = collection.get(ids=list(page_obj), include=["metadatas"])
    except Exception as e:
        return render(request, "assistant/admin-vector-error.html", {
            "message": f"Erro ao buscar documentos da página: {str(e)}"
        })

    documentos = []
    for id_, metadata in zip(resultados['ids'], resultados['metadatas']):
        metadata = {k.replace(" ", "_"): v for k, v in metadata.items()}
        doc = {'id': id_}
        doc.update(metadata)
        documentos.append(doc)

    print(documentos[0])

    return render(request, "assistant/admin-vector-base.html", {
        "page_obj": page_obj,  # ainda contém os IDs paginados
        "documentos": documentos  # os documentos reais da página
    })