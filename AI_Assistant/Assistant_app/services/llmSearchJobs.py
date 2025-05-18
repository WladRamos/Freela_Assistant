from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os
from Assistant_app.services.llmReviewer import stream_reviewed_answer

env_file = find_dotenv()
load_dotenv(env_file)
gpt_key = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

system = """Voce é um assistente inteligente projetado para ajudar programadores freelancers. 
Com base no pedido do usuário, nas suas informações pessoais e nos trabalhos encontrados, liste para o usuário as opções de trabalhos que ele possui.
Liste na resposta apenas os trabalhos que fazem sentido com o pedido do usuário.
Deixe sempre claro qual é o site que o trabalho pertence.
Tente sempre citar o motivo pelo qual você está sugerindo aquele trabalho.
fique atento a moeda que o orçamento do trabalho esta especificado. Sempre que possível, faça a conversão para dolár, e sempre utilize os simbolos internacionais de moeda. Por exemplo real (R$), euro (€), dólar (US$), etc.
Sempre mostre todas as informações disponiveis sobre orçamento do trabalho, incluindo preço mínimo e preço máximo sempre que estiverem disponíveis.
Escreva sua resposta em markdown.
"""

def stream_llm_response_search(user_message, jobs_found, user_info, context):

    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_message}\n\nUser info: {user_info}\n\nJobs found: {jobs_found}"

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
        extra_context=jobs_found,
        original_answer=original_response
    ):
        yield chunk

    