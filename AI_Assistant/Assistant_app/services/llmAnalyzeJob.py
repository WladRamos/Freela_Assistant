from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os
import chromadb
import re
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path

# Carregar variáveis de ambiente
env_file = find_dotenv()
load_dotenv(env_file)
gpt_key = os.getenv('OPENAI_API_KEY')

# Inicializar LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

def extract_title(response):
    """Extrai o título do trabalho gerado pelo LLM corretamente."""
    match = re.search(r'```resposta\s*\n*(.*?)\n*```', response, re.DOTALL)
    return match.group(1).strip() if match else response.strip()

def format_job_info(job_dict):
    """Formata as informações de um trabalho para exibição organizada."""
    job_info = "-" * 80 + "\n"
    job_info += f"Job Title: {job_dict.get('Job Title', 'N/A')}\n"
    job_info += f"Search Keyword: {job_dict.get('Search_Keyword', 'N/A')}\n"
    
    for i in range(1, 10):
        category_key = f'Category_{i}'
        if job_dict.get(category_key):
            job_info += f"{category_key}: {job_dict[category_key]} "

    job_info += "\n"
    job_info += f"Experience Level: {job_dict.get('EX_level_demand', 'N/A')}\n"
    job_info += f"Time Limitation: {job_dict.get('Time_Limitation', 'N/A')}\n"
    job_info += f"Payment Type: {job_dict.get('Payment_type', 'N/A')}\n"

    if job_dict.get('Payment_type') == 'Fixed-price':
        job_info += f"Cost: {job_dict.get('Job_Cost', 'N/A')} {job_dict.get('Currency', 'N/A')}\n"
    elif job_dict.get('Payment_type') == 'Hourly':
        job_info += f"Hourly Rate: {job_dict.get('Hourly_Rate', 'N/A')} {job_dict.get('Currency', 'N/A')}\n"

    job_info += f"Min Price: {job_dict.get('Min_price', 'N/A')} | Max Price: {job_dict.get('Max_price', 'N/A')} | Avg Price: {job_dict.get('Avg_price', 'N/A')}\n"
    job_info += f"Description: {job_dict.get('Description', 'N/A')}\n"
    job_info += "-" * 80 + "\n"

    return job_info

def get_similar_jobs(user_input):
    """Gera um título para o trabalho do usuário, busca trabalhos similares na base vetorial e retorna os resultados formatados."""

    # Prompt para gerar o título em inglês
    prompt_titulo = ChatPromptTemplate.from_messages([
        ("system", """Você receberá uma descrição de um trabalho freelancer e deverá gerar um título em inglês para ele.
        Se um título já estiver presente na descrição, utilize-o. Caso contrário, crie um novo título adequado.
        Retorne apenas o título dentro de ```resposta```."""),
        ("user", "Segue a descrição do trabalho:\n{trabalho}")
    ])

    # Gerar título usando LLM
    chain_titulo = prompt_titulo | llm
    titulo_gerado = chain_titulo.invoke({"trabalho": user_input}).content
    titulo_ingles = extract_title(titulo_gerado)

    # Conectar ao banco vetorial (ChromaDB)
    base_dir = Path(__file__).resolve().parent.parent  # Sobe dois níveis para a raiz do projeto
    caminho_persistent_client = base_dir.parent  # Sobe mais um nível para alcançar o banco vetorial

    # Criar cliente persistente do ChromaDB
    client = chromadb.PersistentClient(path=str(caminho_persistent_client))

    try:
        collection = client.get_collection("Base_de_Trabalhos")
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar a base de dados: {str(e)}")

    # Buscar trabalhos similares no banco vetorial
    try:
        results = collection.query(query_texts=[titulo_ingles], n_results=10)
        trabalhos_encontrados = results.get('metadatas', [[]])[0]

        if not trabalhos_encontrados:
            return "Nenhum trabalho semelhante encontrado na base de dados."

        # Formatar os trabalhos encontrados
        trabalhos_formatados = "\n".join([format_job_info(trab) for trab in trabalhos_encontrados])

        return trabalhos_formatados
    except Exception as e:
        return f"Erro ao buscar trabalhos na base vetorial: {str(e)}"

system = """Você é um assistente inteligente projetado para ajudar programadores freelancers. 
Com base nas informações do(s) trabalho(s) enviado(s) pelo usuário, faça uma análise, comparando-os com os trabalhos semelhantes obtidos da base de dados do sistema.
Sua análise deve ser feita com o objetivo de responder a pergunta do usuário com relação ao trabalho enviado.
A solicitação do usuário pode ter relação com suas informações pessoais, como trabalhos do seu histórico, habilidades, etc. Você receberá essas informações junto ao pedido do usuário.
Caso os trabalhos recebidos da base não tenham relação suficiente com os enviados pelo usuário, informe que não foi possível encontrar trabalhos semelhantes.
Escreva sua resposta em markdown.
"""

def get_llm_response_analyze(user_message, user_info, context):
    """Determina a resposta baseada na consulta do usuário e nos trabalhos similares encontrados."""
    
    similar_jobs = get_similar_jobs(user_message)
    print(similar_jobs)

    # Se não houver trabalhos semelhantes, já retorna essa informação
    if "Nenhum trabalho semelhante encontrado" in similar_jobs:
        return "Não foi possível encontrar trabalhos semelhantes na base de dados. Tente reformular sua busca."

    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_message}\n\nUser info: {user_info}\n\nSimilar Jobs: {similar_jobs}"
    print(prompt)
    response = llm.invoke(input=prompt)

    return response.content
