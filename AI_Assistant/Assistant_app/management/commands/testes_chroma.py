from django.core.management.base import BaseCommand
import openai
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate


class Command(BaseCommand):
    help = 'Testa integração do chroma com o gpt'

    def handle(self, *args, **options):

        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        base_dir = Path(__file__).resolve().parent.parent.parent
        caminho_persistent_client = base_dir.parent

        # Configurando embeddings e o vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(persist_directory=str(caminho_persistent_client), embedding_function=embeddings)

        # Criando o retriever a partir do vectorstore
        retriever = vectorstore.as_retriever()

        # Configurando o LLM (modelo de linguagem)
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        def chatbot(usuario_input):
            print("Entrei 1")
            # Recupera documentos relevantes do vector store
            docs = retriever.invoke(usuario_input)
            print("Entrei 2")

            # Prepara o contexto para o prompt
            context = "\n\nContexto:\n" + "\n".join([doc.page_content for doc in docs])
            prompt = usuario_input + context

            # Gera a resposta usando o contexto recuperado
            resposta = llm.invoke(prompt)
            print("Entrei 3")

            return resposta

        # Exemplo de uso
        usuario_input = """Descreva as informações do job que mais se encaixa com as especificações do usuário:

        Especificação do usuário: Gostaria de um trabalho que pague por hora para fazer uma landing page.
        """
        resposta = chatbot(usuario_input)
        print(resposta)
