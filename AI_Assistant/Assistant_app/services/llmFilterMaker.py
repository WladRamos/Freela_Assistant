from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from Assistant_app.models import User, Habilidade, UsuarioHabilidade, ProjetoHistorico, ProjetoHabilidade
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
            "valor_pagamento_dolar": projeto.valor_pagamento,
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
    A user_info sempre irá conter as informações de habilidades, preferencias de preços e historico de trabalhos. Cabe a voce decidir como e quais informações usar para gerar os filtros.

    Exemplos:
    - Mensagem: "Estou procurando um trabalho de programação em Python."
    - user_info: "Habilidades": ["Python", "Java", "C++", "Machine Learning"],
                  "Preferências de preço": 'preco_hora_min': 10, 'preco_fixo_min': 100,
                  "Historico de trabalhos": ['titulo': 'Desenvolvimento de site', 'descricao': 'Desenvolvimento de site comercial utilizando django', 'tipo_pagamento': 'Hora', 'valor_pagamento_dolar': 20, 'habilidades': ['Python', 'Django', 'HTML', 'CSS']]

      -> Filtros gerados: "programming", "Python"
    
    - Mensagem: "Busco trabalhos semelhantes aos que já fiz."
    - user_info: "Historico de trabalhos": ['titulo': 'Desenvolvimento de site', 'descricao': 'Desenvolvimento de site comercial utilizando django', 'tipo_pagamento': 'Hora', 'valor_pagamento_dolar': 20, 'habilidades': ['Python', 'Django', 'HTML', 'CSS']]
        -> Filtros gerados: "Web development", "Django", "HTML", "CSS"
    
    - Mensagem: "Gostaria de encontrar trabalhos consizentes com minhas habilidades."
    - user_info: "Habilidades": ["Python", "Java", "C++", "Machine Learning"]
        -> Filtros gerados: "Python", "Java", "C++", "Machine Learning"
    
    Agora, gere os filtros para a mensagem do usuário e as informações fornecidas.
    """),
    ("user", """
     - Mensagem: {user_message}\n
     - user_info: {user_info}
     """)
    ])

    chain_filter = prompt_filter | llm
    filtro_bruto = chain_filter.invoke({"user_message": user_message, "user_info": user_info}).content.strip()

    try:
        return re.findall(r'"(.*?)"', filtro_bruto)
    except:
        return None