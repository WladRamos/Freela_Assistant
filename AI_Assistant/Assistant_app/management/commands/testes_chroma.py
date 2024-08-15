from django.core.management.base import BaseCommand
import openai
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import chromadb
import re

PROMPT_QUERY_ANALISE = """"
Você será responsável por receber detalhes sobre um trabalho de freelance na área de programação e responder com um possível título para esse trabalho.
Esse título será Utilizado para fazer uma pesquisa para encontrar trabalhos semelhantes.

    Instruções:

    1. Caso na descrição do trabalho informado ja tenha um título para o trabalho, você pode utilizá-lo como resposta.

    2. Sua resposta deve conter o título para o trabalho na sua língua original e também em inglês, separados por um '-'. Caso a língua original ja seja inglês, deverá ser retornado apenas um título.

    3. Sua resposta deve estar formatada da seguinte forma:

    ```resposta
    Título em Inglês - Título na Língua Original
    ```
"""

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

        # Configurando o LLM (modelo de linguagem)
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        def coleta_titulo(titulo):
            padrao = r'```resposta(.*?)```'
            resultado = re.search(padrao, titulo, re.DOTALL)
            
            if resultado:
                return resultado.group(1).strip()
            else:
                return titulo


        def chatbot(usuario_input):

            prompt_titulo = PROMPT_QUERY_ANALISE + usuario_input

            titulos = coleta_titulo(llm(prompt_titulo).content).split("-")

            print("Titulo Recebido pela LLM")
            print(titulos)

            for titulo in titulos:
                results = collection.query(
                    query_texts=[titulo],
                    n_results=5
                )
                docs = results # Acessa a lista de documentos retornada
                print(docs)

                if not docs:
                    return "Nenhum documento relevante encontrado."

            # Prepara o contexto para o prompt
            #context = "\n\nContexto:\n" + "\n".join(docs)
            #prompt = usuario_input + context

            # Gera a resposta usando o contexto recuperado
            #resposta = llm(prompt)
            #return resposta

        # Exemplo de uso
        usuario_input = """
            SMS with link shortening + Linux Admin
            Posted 5 minutes ago
            Worldwide
            Im looking to create a simple system for now. The simple system will be sending and receiving SMS messages and using our own(that you need to create) link shortening service.

            I noticed that backend devs are usually not so good wit front-end and thats fine ill get a designer and front-end developer separately.

            For backend i prefer if you know basic Linux administration, DB administration,.

            Bonus if you have experience with GSM Modems or SMS API.



            More than 30 hrs/week
            Hourly
            Intermediate
            Experience Level
            $20.00-$45.00 Hourly
            Remote Job
            Ongoing project
            Project Type
            Contract-to-hire
            This job has the potential to turn into a full time role
        """
        resposta = chatbot(usuario_input)
        print(resposta)
