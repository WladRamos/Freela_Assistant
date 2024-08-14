from django.core.management.base import BaseCommand
import openai
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import chromadb

class Command(BaseCommand):
    help = 'Testa integração do chroma com o gpt'

    def handle(self, *args, **options):

        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        base_dir = Path(__file__).resolve().parent.parent.parent
        caminho_persistent_client = base_dir.parent

        # Conectar à coleção existente no Chroma DB
        client = chromadb.PersistentClient(path=str(caminho_persistent_client))
        collection = client.get_collection("Base_de_Trabalhos")

        # Configurando embeddings
        embeddings = OpenAIEmbeddings()

        # Configurando o LLM (modelo de linguagem)
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        def chatbot(usuario_input):
            print("Verificando documentos no vector store...")

            # Executa a busca diretamente na coleção
            results = collection.query(
                query_texts=[usuario_input],
                n_results=5  # Especifique quantos resultados você quer retornar
            )
            
            docs = results['documents'][0]  # Acessa a lista de documentos retornada
            print(f"Documentos encontrados: {len(docs)}")
            for doc in docs:
                print(doc)

            if not docs:
                return "Nenhum documento relevante encontrado."

            # Prepara o contexto para o prompt
            context = "\n\nContexto:\n" + "\n".join(docs)
            prompt = usuario_input + context

            # Gera a resposta usando o contexto recuperado
            resposta = llm(prompt)
            return resposta

        # Exemplo de uso
        usuario_input = """Descreva as informações do job que mais se encaixa com as especificações do usuário:

        Especificação do usuário: Gostaria de um trabalho que pague por hora para fazer uma landing page.
        """
        resposta = chatbot(usuario_input)
        print(resposta)
