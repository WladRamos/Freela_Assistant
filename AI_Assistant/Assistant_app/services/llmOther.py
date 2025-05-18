from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os
from Assistant_app.services.llmReviewer import stream_reviewed_answer

env_file = find_dotenv()
load_dotenv(env_file)
gpt_key = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

system = """Voce é um assistente inteligente projetado para ajudar programadores freelancers. 
Você faz parte de um sistema que possui funcionalidades para busca de trabalhos, análise de trabalhos e dicas para freelancers.
A sua função é analisar a pergunta/pedido do usuário e entender se ele está fazendo uma requisição fora do escopo do assistente ou se ele está continuando uma conversa que faz sentido no contexto do assistente.
Se o usuário estiver fazendo uma requisição fora do escopo, voce deve responder com a frase: Esta pergunta não está incluída no escopo do assistente.
Se o usuário estiver continuando uma conversa que faz sentido no contexto do assistente, responde-lo com a resposta adequada, continuando a conversa.
Se o usuário estiver te cumprimentando, despedindo ou agradecendo, você deve responder de forma educada e cordial.
Algumas informações sobre o usuário serão passadas junto com a pergunta, e se necessário, você pode usá-las para gerar a resposta que fará sentido para o usuário. Caso contrário apenas ignore as user_infos.
Escreva sua resposta em markdown.
"""

def stream_llm_response_other(user_message, user_info, context):

    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_message}\n\nUser info: {user_info}"

    print("----------------------------------------")
    print("Prompt:", prompt)
    print("----------------------------------------")

    original_response = llm.invoke(prompt).content

    print("----------------------------------------")
    print("Resposta original:", original_response)
    print("----------------------------------------")

    for chunk in stream_reviewed_answer(
        user_question=user_message,
        user_info=user_info,
        context=context,
        extra_context=None,
        original_answer=original_response
    ):
        yield chunk

    