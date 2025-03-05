from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from Assistant_app.services.router import get_router_decision
from Assistant_app.services.ClassJobFetch import JobFetcher
from Assistant_app.services.llmSearchJobs import get_llm_response_search
from Assistant_app.services.llmAnalyzeJob import get_llm_response_analyze
from Assistant_app.services.llmTips import answer_user_question
import json

def index(request):
    return render(request, "assistant/index.html")
    
def chat_llm(request):
    if request.method == "POST":

        data = json.loads(request.body)
        user_message = data.get('message')

        router_decision = get_router_decision(user_message)

        #Busca de trabalhos
        if router_decision == "search_jobs":
            jobs = JobFetcher()
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