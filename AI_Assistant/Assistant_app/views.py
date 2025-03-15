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
from .models import User, ProjetoHistorico, UsuarioHabilidade, Habilidade, ProjetoHabilidade
from django.contrib.auth.decorators import login_required

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

        router_decision = get_router_decision(user_message)

        #Busca de trabalhos
        if router_decision == "search_jobs":
            jobs = JobFetcher() #começar a usar filtros
            jobs_str = jobs.get_jobs_str()
            if jobs_str:
                response = get_llm_response_search(user_message, jobs.get_jobs_str(), None) # add user info
                if not response:
                    response = 'Não foi possivel encontrar trabalhos no momento.'
            else:
                response = 'Não foi possivel encontrar trabalhos no momento.'

        #Análise de trabalho
        elif router_decision == "analyze_job":
            response = get_llm_response_analyze(user_message, None) # add user info
            if not response:
                response = 'Não foi possivel analisar o trabalho no momento.'

        #Dicas de freelancing/programação
        elif router_decision == "freelancing_tips":
            response = answer_user_question(user_message)
            if not response:
                response = 'Não foi possivel encontrar dicas no momento.'
        
        else:
            response = "Esta pergunta não está incluida no escopo do assistente."

        return JsonResponse({"response": response}, status =200)
    else:
        return JsonResponse({"error": "Post not found."}, status=404)
    

@login_required
def editar_perfil(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = request.user

            # Atualiza preços
            user.preco_fixo_min = float(data.get("preco_fixo_min", user.preco_fixo_min))
            user.preco_hora_min = float(data.get("preco_hora_min", user.preco_hora_min))
            user.save()

            # Atualiza trabalhos
            for trabalho in data.get("trabalhos", []):
                ProjetoHistorico.objects.update_or_create(
                    id=trabalho.get("id"),
                    defaults={
                        "usuario": user,
                        "titulo": trabalho["titulo"],
                        "descricao": trabalho["descricao"],
                        "tipo_pagamento": trabalho["tipo_pagamento"],
                        "valor_pagamento": trabalho["valor_pagamento"]
                    }
                )

            # Atualiza habilidades
            UsuarioHabilidade.objects.filter(usuario=user).delete()
            for skill in data.get("habilidades", []):
                habilidade, _ = Habilidade.objects.get_or_create(nome=skill)
                UsuarioHabilidade.objects.create(usuario=user, habilidade=habilidade)

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Método não permitido"})

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