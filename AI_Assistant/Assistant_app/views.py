from django.shortcuts import render
from django.urls import reverse
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseRedirect
from django.db import IntegrityError
from Assistant_app.services.router import get_router_decision
from Assistant_app.services.ClassJobFetch import JobFetcher
from Assistant_app.services.llmSearchJobs import stream_llm_response_search
from Assistant_app.services.llmAnalyzeJob import stream_llm_response_analyze
from Assistant_app.services.llmTips import stream_answer_user_question
from Assistant_app.services.llmOther import stream_llm_response_other
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
import uuid

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

        if not chat_id:
            titulo_chat = generate_chat_title(user_message)
            chat = Chat.objects.create(usuario=request.user, nome=titulo_chat or "Nova Conversa")
            contexto = ""
        else:
            chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)
            contexto = gerar_contexto_conversa(chat)

        mensagem = Mensagem.objects.create(chat=chat, conteudo=user_message)

        router_decision = get_router_decision(user_message)
        user_info = get_user_info(request.user.id)

        def event_stream():
            full_response = ""

            def stream_and_capture(generator):
                nonlocal full_response
                buffer = ""

                for chunk in generator:
                    full_response += chunk
                    buffer += chunk

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if not line:
                            continue

                        if line.startswith("#"):
                            yield f"data: {line}\n\n"
                            yield f"data: \n\n"
                        else:
                            yield f"data: {line}\n\n"

                if buffer.strip():
                    yield f"data: {buffer.strip()}\n\n"

            if router_decision == "search_jobs":
                filters = generate_filter(user_message, user_info)
                jobs = JobFetcher(filters)
                jobs_str = jobs.get_jobs_str()
                if not jobs_str:
                    yield "data: Não foi possível encontrar trabalhos no momento.\n\n"
                    return
                yield from stream_and_capture(
                    stream_llm_response_search(user_message, jobs_str, user_info, contexto)
                )
            elif router_decision == "analyze_job":
                yield from stream_and_capture(
                    stream_llm_response_analyze(user_message, user_info, contexto)
                )
            elif router_decision == "freelancing_tips":
                yield from stream_and_capture(
                    stream_answer_user_question(user_message, user_info, contexto)
                )
            else:
                yield from stream_and_capture(
                    stream_llm_response_other(user_message, user_info, contexto)
                )

            RespostaAssistente.objects.create(mensagem=mensagem, conteudo=full_response)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["X-Chat-Id"] = str(chat.id)
        return response

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
        habilidade, _ = Habilidade.objects.get_or_create(nome=skill_name)
        _, criada = UsuarioHabilidade.objects.get_or_create(usuario=user, habilidade=habilidade)

        return JsonResponse({"success": True, 
                             "habilidade_id": habilidade.id,
                             "nova": criada
                             })

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

    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    try:
        collection = client.get_collection("Base_de_Trabalhos")

        if search_query:
            resultados = collection.query(
                query_texts=[search_query],
                n_results=1000,
                include=["metadatas"]
            )
            documentos = []
            for id_, metadata in zip(resultados['ids'][0], resultados['metadatas'][0]):
                metadata = {k.replace(" ", "_"): v for k, v in metadata.items()}
                doc = {"id": id_}
                doc.update(metadata)
                documentos.append(doc)
        else:
            all_data = collection.get(include=["metadatas"])
            documentos = []
            for id_, metadata in zip(all_data['ids'], all_data['metadatas']):
                metadata = {k.replace(" ", "_"): v for k, v in metadata.items()}
                doc = {"id": id_}
                doc.update(metadata)
                documentos.append(doc)

    except Exception as e:
        return render(request, "assistant/admin-vector-error.html", {
            "message": f"Erro ao acessar a base vetorial: {str(e)}"
        })

    paginator = Paginator(documentos, 50)
    page_obj = paginator.get_page(page_number)

    return render(request, "assistant/admin-vector-base.html", {
        "page_obj": page_obj,
        "documentos": page_obj.object_list,
        "search_query": search_query,
    })


@user_passes_test(lambda u: u.tipo_usuario == 'Administrador')
def admin_adicionar_trabalho(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            job_title = data.get("jobTitle", "").strip()
            description = data.get("description", "").strip()
            valores = [
                data.get("cost", "").strip(),
                data.get("hourly", "").strip(),
                data.get("min", "").strip(),
                data.get("max", "").strip(),
                data.get("avg", "").strip(),
            ]

            if not job_title or not description or not any(valores):
                return JsonResponse({"success": False, "message": "Preencha o título, descrição e pelo menos um valor de pagamento."}, status=400)

            categorias = data.get("categories", [])

            metadados = {
                "Job Title": job_title,
                "EX_level_demand": data.get("exLevel", ""),
                "Time_Limitation": data.get("timeLimit", ""),
                "Search_Keyword": data.get("keyword", ""),
                "Description": description,
                "Category_1": categorias[0] if len(categorias) > 0 else "",
                "Category_2": categorias[1] if len(categorias) > 1 else "",
                "Category_3": categorias[2] if len(categorias) > 2 else "",
                "Category_4": categorias[3] if len(categorias) > 3 else "",
                "Category_5": categorias[4] if len(categorias) > 4 else "",
                "Category_6": categorias[5] if len(categorias) > 5 else "",
                "Category_7": categorias[6] if len(categorias) > 6 else "",
                "Category_8": categorias[7] if len(categorias) > 7 else "",
                "Category_9": categorias[8] if len(categorias) > 8 else "",
                "Payment_type": data.get("payment", ""),
                "Job_Cost": data.get("cost", ""),
                "Hourly_Rate": data.get("hourly", ""),
                "Currency": data.get("currency", ""),
                "Min_price": data.get("min", ""),
                "Max_price": data.get("max", ""),
                "Avg_price": data.get("avg", "")
            }

            base_dir = Path(__file__).resolve().parent
            caminho_persistent_client = base_dir.parent
            client = chromadb.PersistentClient(path=str(caminho_persistent_client))
            collection = client.get_collection("Base_de_Trabalhos")

            collection.add(
                documents=[job_title],
                metadatas=[metadados],
                ids=[str(uuid.uuid4())]
            )

            return JsonResponse({"success": True, "message": "Trabalho adicionado com sucesso."})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erro ao adicionar trabalho: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Método não permitido."}, status=405)



def admin_atualizar_trabalho(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_ = data.get("id")
            if not id_:
                return JsonResponse({"success": False, "message": "ID não fornecido."}, status=400)

            categorias = data.get("categories", [])

            metadados = {
                "Job Title": data.get("jobTitle", ""),
                "EX_level_demand": data.get("exLevel", ""),
                "Time_Limitation": data.get("timeLimit", ""),
                "Search_Keyword": data.get("keyword", ""),
                "Description": data.get("description", ""),
                "Category_1": categorias[0] if len(categorias) > 0 else "",
                "Category_2": categorias[1] if len(categorias) > 1 else "",
                "Category_3": categorias[2] if len(categorias) > 2 else "",
                "Category_4": categorias[3] if len(categorias) > 3 else "",
                "Category_5": categorias[4] if len(categorias) > 4 else "",
                "Category_6": categorias[5] if len(categorias) > 5 else "",
                "Category_7": categorias[6] if len(categorias) > 6 else "",
                "Category_8": categorias[7] if len(categorias) > 7 else "",
                "Category_9": categorias[8] if len(categorias) > 8 else "",
                "Payment_type": data.get("payment", ""),
                "Job_Cost": data.get("cost", ""),
                "Hourly_Rate": data.get("hourly", ""),
                "Currency": data.get("currency", ""),
                "Min_price": data.get("min", ""),
                "Max_price": data.get("max", ""),
                "Avg_price": data.get("avg", "")
            }

            base_dir = Path(__file__).resolve().parent
            caminho_persistent_client = base_dir.parent
            client = chromadb.PersistentClient(path=str(caminho_persistent_client))
            collection = client.get_collection("Base_de_Trabalhos")

            collection.update(
                ids=[id_],
                documents=[data.get("jobTitle", "")],
                metadatas=[metadados]
            )

            return JsonResponse({"success": True, "message": "Trabalho atualizado com sucesso."})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Método não permitido."}, status=405)


@user_passes_test(lambda u: u.tipo_usuario == 'Administrador')
def admin_deletar_trabalhos(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])

            if not ids:
                return JsonResponse({"success": False, "message": "Nenhum ID fornecido."}, status=400)

            base_dir = Path(__file__).resolve().parent
            caminho_persistent_client = base_dir.parent
            client = chromadb.PersistentClient(path=str(caminho_persistent_client))
            collection = client.get_collection("Base_de_Trabalhos")

            collection.delete(ids=ids)

            return JsonResponse({"success": True, "message": "Trabalhos excluídos com sucesso."})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erro: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Método não permitido."}, status=405)
