from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

def index(request):
    return render(request, "assistant/index.html")

def chat_llm(request):
    if request.method == "POST":

        response = 'BlaBlaBla...'
        return JsonResponse({"response": response})
    else:
        return JsonResponse({"error": "Post not found."}, status=404)