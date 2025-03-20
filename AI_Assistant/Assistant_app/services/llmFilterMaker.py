from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from AI_Assistant.Assistant_app.models import User, Habilidade, UsuarioHabilidade, ProjetoHistorico, ProjetoHabilidade
from dotenv import load_dotenv, find_dotenv
from django.shortcuts import get_object_or_404
import os
import getpass
import re

# Carregar variáveis de ambiente
env_file = find_dotenv()
load_dotenv(env_file)

gpt_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

def get_user_info(user_id):
    """Function to get the user information from the database and create a dictionary."""
    
    user = get_object_or_404(User, id=user_id)
    
    # Pegando as habilidades do usuário
    habilidades = list(user.habilidades.values_list("habilidade__nome", flat=True))

    # Pegando as preferências de preço
    preferencias_preco = {
        "preco_hora_min": user.preco_hora_min,
        "preco_fixo_min": user.preco_fixo_min,
    }

    # Pegando os 5 projetos mais recentes com habilidades vinculadas
    historico_trabalhos = []
    projetos = user.projetos.order_by("-data")[:5]

    for projeto in projetos:
        habilidades_projeto = list(projeto.habilidades.values_list("habilidade__nome", flat=True))
        historico_trabalhos.append({
            "titulo": projeto.titulo,
            "descricao": projeto.descricao,
            "tipo_pagamento": projeto.tipo_pagamento,
            "valor_pagamento": projeto.valor_pagamento,
            "data": projeto.data,
            "habilidades": habilidades_projeto,
        })

    return {
        "habilidades": habilidades,
        "preferencias_preco": preferencias_preco,
        "historico_trabalhos": historico_trabalhos,
    }


def generate_filter(user_message, user_info):
    """Function to generate the filter based on the user query and user personal information."""
    prompt_filter = ChatPromptTemplate.from_messages([
    ("system", """Você é responsável por gerar uma lista de filtros para buscar trabalhos.
    Com base na mensagem do usuário e nas informações de habilidades, preferencias de preços e historico de trabalhos, gere um filtro para buscar trabalhos.
    Sua resposta deve conter os filtros em inglês entre aspas duplas, separando cada filtro por virgula.

    Exemplos:
    - Mensagem: "Estou procurando um trabalho de programação em Python."
      -> Filtros gerados: "programming", "Python"
    
    - Mensagem: "Busco trabalhos semelhantes aos que já fiz."
    - user_info: Histotico de trabalhos: "Desenvolvimento de aplicativos móveis, Desenvolvimento web, Design gráfico"
        -> Filtros gerados: "Mobile app development", "Web development", "Graphic design"
    
    - Mensagem: "Gostaria de encontrar trabalhos consizentes com minhas habilidades."
    - user_info: Habilidades: "Python, Java, C++, Machine Learning"
        -> Filtros gerados: "Python", "Java", "C++", "Machine Learning"
    """),
    ("user", user_message),
    ("user_info", user_info)
    ])

    chain_filter = prompt_filter | llm
    filtro_bruto = chain_filter.invoke({"message": user_message, "user_info": user_info}).content.strip()

    try:
        return re.search(r'"([^"]*)"', filtro_bruto)
    except:
        return None