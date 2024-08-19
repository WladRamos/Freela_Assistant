from django.core.management.base import BaseCommand
import openai
from langchain_openai import ChatOpenAI
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

    Segue o trabalho que você deverá dar o título:
    
"""

class Command(BaseCommand):
    help = 'Testa integração do chroma com o gpt'

    def handle(self, *args, **options):

        #Configurando LLM
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        # Conectar ao chroma
        base_dir = Path(__file__).resolve().parent.parent.parent
        caminho_persistent_client = base_dir.parent
        client = chromadb.PersistentClient(path=str(caminho_persistent_client))
        collection = client.get_collection("Base_de_Trabalhos")
        
        def formatar_info_trabalho(job_dict):
            job_info = "-" * 80
            job_info += "\n"
            job_info += f"Job Title: {job_dict.get('Job Title', 'N/A')}\n"
            
            job_info += f"Search Keyword: {job_dict.get('Search_Keyword', 'N/A')}\n"
            
            for i in range(1, 10):
                category_key = f'Category_{i}'
                if job_dict.get(category_key):
                    job_info += f"{category_key}: {job_dict[category_key]} "
            
            job_info += "\n"
            
            if 'EX_level_demand' in job_dict:
                job_info += f"Experience Level: {job_dict['EX_level_demand']}\n"
                
            job_info += f"Payment Type: {job_dict.get('Payment_type', 'N/A')}\n"
            
            if job_dict.get('Payment_type') == 'Fixed-price':
                job_info += f"Cost: {job_dict.get('Job_Cost', 'N/A')}\n"
            elif job_dict.get('Payment_type') == 'Hourly':
                job_info += f"Hourly Rate: {job_dict.get('Hourly_Rate', 'N/A')}\n"

            job_info += f"Description: {job_dict.get('Description', 'N/A')}\n"

            job_info += "-" * 80

            return job_info
        

        def coleta_titulo(titulo):
            padrao = r'```resposta(.*?)```'
            resultado = re.search(padrao, titulo, re.DOTALL)
            
            if resultado:
                return resultado.group(1).strip()
            else:
                return titulo


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

        prompt_titulo = PROMPT_QUERY_ANALISE + usuario_input

        titulos = coleta_titulo(llm.invoke(prompt_titulo).content).split("-")

        for titulo in titulos:
            titulo = titulo.strip()
            results = collection.query(
                query_texts=[titulo],
                n_results=5
            )
            trabalhos = results['metadatas'][0]

            for trab in trabalhos:
                print(formatar_info_trabalho(trab))
        
