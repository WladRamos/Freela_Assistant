from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from dotenv import load_dotenv, find_dotenv
import os
import getpass

# Carregar variáveis de ambiente
env_file = find_dotenv()
load_dotenv(env_file)

# Configurar chave Tavily
tavily_key = os.environ.get("TAVILY_API_KEY")
if not tavily_key:
    tavily_key = getpass.getpass("Tavily API key:\n")

# Inicializar Tavily Client
tavily_client = TavilyClient(api_key=tavily_key)

# Inicializar LLM
gpt_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=gpt_key)

# Lista de sites permitidos para busca no Tavily
ALLOWED_DOMAINS = [
    "https://www.upwork.com/resources",
    "https://www.freelancer.com/articles",
    "https://www.guru.com/blog/"
]

def generate_search_query(user_question, user_info):
    """Gera uma frase em inglês otimizada para a busca."""
    
    prompt_search_query = ChatPromptTemplate.from_messages([
        ("system", """Você receberá uma pergunta de um usuário e deverá gerar uma frase curta e clara em inglês 
        que será usada para buscar artigos sobre o assunto. A frase gerada não precisa ser uma tradução literal, 
        mas deve capturar a intenção principal da pergunta.
        Um conjunto de informações do usuário serão passadas junto com a pergunta, e você pode usá-las para gerar a frase que será usada na busca, caso faça sentido.
        Apenas use as informações do usuário se a pergunta fizer referência a elas.

        Exemplos:
        - Pergunta: "Boa noite, gostaria de entender melhor como funcionam os frameworks, para que servem, etc. Pois estou tendo dúvidas para iniciar o meu projeto."
          -> Frase gerada: "How do frameworks work?"
        
        - Pergunta: "Quais são as melhores linguagens para desenvolvimento web?"
          -> Frase gerada: "Best programming languages for web development"

        - Pergunta: "Sou freelancer e quero dicas para conseguir mais clientes."
          -> Frase gerada: "How to get more clients as a freelancer?"
        
        Gere uma única frase objetiva para a seguinte pergunta:"""),
        ("user", """"
            - Mensagem: {question}\n
            - user_info: {user_info}
         """)])

    chain_search_query = prompt_search_query | llm

    query = chain_search_query.invoke({"question": user_question, "user_info": user_info}).content.strip()
    query = query.strip('"').strip("'")
    return query

def search_articles_with_tavily(question_in_english):
    """Usa Tavily para buscar artigos apenas nos sites permitidos."""
    
    response = tavily_client.search(
        query=question_in_english,
        include_answer='advanced',
        search_depth='advanced'
    )

    return response

def format_results(search_response):
    """Formata os resultados encontrados no Tavily para servir como contexto."""
    
    if not search_response:
        return "Não encontrei informações relevantes"

    context = "### Resumo da Pesquisa\n"

    # 🔹 Se houver uma resposta direta do Tavily, usá-la
    if "answer" in search_response and search_response["answer"]:
        context += f"**{search_response['answer']}**\n\n"

    # 🔹 Listar os artigos encontrados
    context += "### Artigos relacionados:\n"
    for result in search_response.get("results", []):
        title = result.get("title", "Título não disponível")
        url = result.get("url", "#")
        content = result.get("content", "Sem descrição disponível.")
        context += f"- **[{title}]({url})**\n  - {content}\n\n"

    return context

system = """Baseado nos seguintes trechos de artigos e informações coletadas, responda à pergunta do usuário.
Um conjunto de informações do usuário será passado junto com a pergunta, e você pode usá-las caso necessário.
Escreva sua resposta de forma clara e objetiva, utilizando markdown para formatação.
Caso existam links relevantes no Search context, inclua-os no final da resposta, numa seção 'Fontes'."""

def generate_final_answer(user_question, search_context, user_info, context):
    """Usa GPT-4o-mini para gerar a resposta final com base nas informações do Tavily."""
    
    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_question}\n\nUser info: {user_info}\n\nSearch context: {search_context}"
    print(prompt)

    response = llm.invoke(input=prompt)
    return response.content

def stream_answer_user_question(user_question, user_info, context):
    question_in_english = generate_search_query(user_question, user_info)
    search_response = search_articles_with_tavily(question_in_english)
    search_context = format_results(search_response)
    print(search_context)

    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_question}\n\nUser info: {user_info}\n\nSearch context: {search_context}"

    for chunk in llm.stream(prompt):
        yield chunk.content
