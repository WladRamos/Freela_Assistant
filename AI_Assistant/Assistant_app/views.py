from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db import IntegrityError
from Assistant_app.services.router import get_router_decision
from Assistant_app.services.ClassJobFetch import JobFetcher
from Assistant_app.services.llmSearchJobs import get_llm_response_search
from Assistant_app.services.llmAnalyzeJob import get_llm_response_analyze
from Assistant_app.services.llmTips import answer_user_question
import json
from django.contrib.auth import authenticate, login, logout
from .models import User, ProjetoHistorico, UsuarioHabilidade, Habilidade, ProjetoHabilidade, Chat, Mensagem, RespostaAssistente
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "assistant/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "assistant/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "assistant/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "assistant/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "assistant/register.html")

def index(request):
    return render(request, "assistant/index.html")

def profile(request):
    return render(request, "assistant/profile.html")
    
def chat_llm(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get('message')
        chat_id = data.get('chat_id')

        if not request.user.is_authenticated:
            return JsonResponse({"error": "Usuário não autenticado"}, status=403)

        # Criar um novo chat se necessário
        if not chat_id:
            chat = Chat.objects.create(usuario=request.user)
        else:
            chat = get_object_or_404(Chat, id=chat_id, usuario=request.user)

        mensagem = Mensagem.objects.create(chat=chat, conteudo=user_message)

        router_decision = get_router_decision(user_message)

        if router_decision == "search_jobs":
            #jobs = JobFetcher()
            #jobs_str = jobs.get_jobs_str()
            #response = get_llm_response_search(user_message, jobs_str, None) if jobs_str else 'Não foi possível encontrar trabalhos no momento.'
            response= "search_jobs"
        elif router_decision == "analyze_job":
            #response = get_llm_response_analyze(user_message, None) or 'Não foi possível analisar o trabalho no momento.'
            response = "analyze_job"
        elif router_decision == "freelancing_tips":
            #response = answer_user_question(user_message) or 'Não foi possível encontrar dicas no momento.'
            response = "freelancing_tips"
        else:
            response = "Esta pergunta não está incluída no escopo do assistente."

        resposta = RespostaAssistente.objects.create(mensagem=mensagem, conteudo=response)

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