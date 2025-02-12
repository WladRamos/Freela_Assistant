from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from Assistant_app.services.router import get_router_decision
from Assistant_app.services.ClassJobFetch import JobFetcher
from Assistant_app.services.llmSearchJobs import get_llm_response
import json

def index(request):
    return render(request, "assistant/index.html")
    
def chat_llm(request):
    if request.method == "POST":

        data = json.loads(request.body)
        user_message = data.get('message')

        router_decision = get_router_decision(user_message)

        if router_decision == "search_jobs":
            jobs = JobFetcher()
            jobs_str = jobs.get_jobs_str()
            if jobs_str:
                response = get_llm_response(user_message, jobs.get_jobs_str(), None) # add user info
        elif router_decision == "analyze_job":
            response = 'analyze_job...'
        elif router_decision == "freelancing_tips":
            response = 'freelancing_tips...'
        else:
            response = 'other'

        
        return JsonResponse({"response": response}, status =200)
    else:
        return JsonResponse({"error": "Post not found."}, status=404)