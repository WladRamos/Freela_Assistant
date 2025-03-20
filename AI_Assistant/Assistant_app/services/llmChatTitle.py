from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv, find_dotenv
import os
import getpass
import re

# Carregar variáveis de ambiente
env_file = find_dotenv()
load_dotenv(env_file)

gpt_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

def generate_chat_title(user_first_message):
    """Gera um título para o chat com base na primeira mensagem do usuário."""
    
    prompt_chat_title = ChatPromptTemplate.from_messages([
        ("system", """Você receberá uma mensagem de um usuário e deverá gerar um título para o chat com base nessa mensagem.
         Responda sempre no formato: Título gerado: "Título aqui"
        
        Exemplos:
        - Mensagem: "Olá, estou com dúvidas sobre como criar um site. Poderia me ajudar?"
          -> Título gerado: "Ajuda para criar um site"
        
        - Mensagem: "Boa tarde, gostaria de saber mais sobre inteligência artificial."
          -> Título gerado: "Dúvidas sobre inteligência artificial"
        
        - Mensagem: "Olá, estou procurando dicas para estudar programação."
          -> Título gerado: "Dicas para estudar programação"
        
        Gere um título para a seguinte mensagem:"""),
        ("user", "{message}")
    ])

    chain_chat_title = prompt_chat_title | llm
    titulo_bruto = chain_chat_title.invoke({"message": user_first_message}).content.strip()
    
    try:
        return re.search(r'"([^"]*)"', titulo_bruto).group(1)
    except:
        return None