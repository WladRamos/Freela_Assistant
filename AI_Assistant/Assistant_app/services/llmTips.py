from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from dotenv import load_dotenv, find_dotenv
import os
import getpass
from Assistant_app.services.llmReviewer import stream_reviewed_answer

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
        ("system", """Você receberá uma pergunta de um usuário e deverá gerar uma search query clara em inglês 
        que será usada para buscar informações sobre o assunto na internet. A frase gerada não precisa ser uma tradução literal, 
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
    print("Query gerada:", query)
    return query

def search_articles_with_tavily(question_in_english):
    """Usa Tavily para buscar artigos apenas nos sites permitidos."""
    
    response = tavily_client.search(
        query=question_in_english,
        search_depth='advanced',
        time_range='year',
    )

    return response

def format_results(search_response):
    """Formata os resultados encontrados no Tavily para servir como contexto."""
    
    if not search_response:
        return "Não encontrei informações relevantes"

    #context = "### Resumo da Pesquisa\n"

    # 🔹 Se houver uma resposta direta do Tavily, usá-la
    #if "answer" in search_response and search_response["answer"]:
    #    context += f"**{search_response['answer']}**\n\n"

    # 🔹 Listar os artigos encontrados
    context = "### Informações coletadas na internet:\n"
    for result in search_response.get("results", []):
        title = result.get("title", "Título não disponível")
        url = result.get("url", "#")
        content = result.get("content", "Sem descrição disponível.")
        context += f"- **[{title}]({url})**\n  - {content}\n\n"

    return context

system = """Você é um assistente inteligente especializado em ajudar freelancers da área de TI e programação.

Sua tarefa é responder de forma clara, objetiva e útil com base nas **informações coletadas na internet** por meio de uma busca automatizada.

Junto com a pergunta do usuário, você também receberá **informações adicionais sobre o próprio usuário**. Use essas informações para personalizar ou contextualizar melhor sua resposta, se for útil.

- A resposta deve ser **escrita em linguagem natural**, com foco em clareza e utilidade.
- Utilize **formatação Markdown** (como listas, títulos, negrito, etc.) para facilitar a leitura.
- **Não utilize HTML, LaTeX ou outras formas de formatação.**
- Caso existam links relevantes no contexto da busca, adicione-os no final da resposta sob o título **Fontes**.

Se a resposta envolver julgamento, recomendação ou análise, considere o ponto de vista de um freelancer que busca boas oportunidades, eficiência e equilíbrio entre esforço e retorno.
"""

# def generate_final_answer(user_question, search_context, user_info, context):
#     """Usa GPT-4o-mini para gerar a resposta final com base nas informações do Tavily."""
    
#     prompt = f"System: {system}\n\n {context} \n\nHuman: {user_question}\n\nUser info: {user_info}\n\nSearch context: {search_context}"
#     print(prompt)

#     response = llm.invoke(input=prompt)
#     return response.content

def stream_answer_user_question(user_question, user_info, context):
    question_in_english = generate_search_query(user_question, user_info)
    search_response = search_articles_with_tavily(question_in_english)
    search_context = format_results(search_response)

    prompt = f"System: {system}\n\n {context} \n\nHuman: {user_question}\n\nUser info: {user_info}\n\nSearch context: {search_context}"
    print(prompt)

    original_response = llm.invoke(prompt).content
    print("Resposta original:", original_response)
    print("----------------------------------------")

    for chunk in stream_reviewed_answer(
        user_question=user_question,
        user_info=user_info,
        context=context,
        extra_context=search_context,
        original_answer=original_response
    ):
        yield chunk
