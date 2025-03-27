from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os

env_file = find_dotenv()
load_dotenv(env_file)
gpt_key = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

system = """Voce é um assistente inteligente projetado para ajudar programadores freelancers. 
Com base no pedido do usuário, nas suas informações pessoais e nos trabalhos encontrados, liste para o usuário as opções de trabalhos que ele possui.
Liste na resposta apenas os trabalhos que fazem sentido com o seu pedido.
Escreva sua resposta em markdown.
"""

def get_llm_response_search(user_message, jobs_found, user_info, context):
    """Function to determine the response based on the user query and user personal information."""
    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_message}\n\nUser info: {user_info}\n\nJobs found: {jobs_found}"
    print(prompt)
    response = llm.invoke(input=prompt)
    return response.content
    