from django.core.management.base import BaseCommand
import openai
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
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

PROMPT_ANALISE_TRABALHO = """"
Você será responsável por fazer considerações e recomendações sobre trabalhos freelancers na área da tecnologia.
Seu papel é ajudar freelancers a fazer melhores escolhas de trabalho e fechar acordos em condições mais favoraveis.

    Instruções:

    1. Você irá receber informações de um trabalho freelancer que o usuário está considerando fazer.

    2. Você terá acesso à informações de 'trabalhos exemplo' realizados na Upwork, que de acordo com um cálculo, são considerados semelhantes ao trabalho que o freelancer irá te enviar.

    3. Você deverá utilizar seu conhecimento, alinhado aos trabalhos exemplo para fazer recomendações ao freelancer. Essas recomendações podem ser tanto financeiras, quanto relacionadas a tempo ou a tecnologias a serem utilizadas. Leve em consideração a dificuldade, quantidade de trabalho e conhecimento exigido.

    4. Cuidado! Pode ocorrer de trabalhos não semelhantes o suficiente serem enviados como trabalhos exemplo para você, baseie-se apenas em trabalhos minimamente semelhantes.

    5. Seja objetivo nas suas recomendações, apenas fale sobre o que você tem recomendações a fazer.

    6. Sinta-se a vontade para fazer as recomendações que quiser ao usuário, mas caso junto ao trabalho que receber, tenha alguma dúvida específica do usuário, responda-a primeiro.

    Observação: Os trabalhos exemplo estão encapsulados dentro do sistema, e o usuário não possui acesso, por isso, não cite esses trabalhos na sua resposta. Se desejar você pode usar simplesmente 'de acordo com a minha base de dados interna'.
    Observação: Tome cuidado com a diferença entre trabalhos de preço fixo e trabalhos pagos por hora, quando compara-los, não ache que uma pessoa que ganha $100 fixos está ganhando mais do que quem ganha $70 por hora, por exemplo.

    Trabalhos exemplo:
    {trabalhos_exemplo}
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
            HTML / CSS Specialist for Marketing Website
            Posted 51 seconds ago
            Worldwide
            I am looking for a person to assist with building my personal website.
            I have 4 pages in mind, and would like an Specialist to this job.

            $50.00

            Fixed-price
            Intermediate
            Experience Level
            Remote Job
            One-time project
            
            Skills and Expertise
            HTML
            CSS
            Landing Page
            Web Development
        """

        prompt_titulo = ChatPromptTemplate.from_messages([("system", PROMPT_QUERY_ANALISE), ("user", "Segue o trabalho que você deverá dar o título:\n {trabalho}")])
    
        chain_titulo = prompt_titulo | llm

        titulos = coleta_titulo(chain_titulo.invoke({"trabalho": usuario_input}).content).split("-")

        trabalhos_exemplo = ""

        for titulo in titulos:
            titulo = titulo.strip()
            results = collection.query(
                query_texts=[titulo],
                n_results=10
            )
            trabalhos = results['metadatas'][0]

            for trab in trabalhos:
                trabalhos_exemplo += formatar_info_trabalho(trab)

        print(trabalhos_exemplo)

        prompt_analise = ChatPromptTemplate.from_messages([("system", PROMPT_ANALISE_TRABALHO), ("user", "Segue a entrada do usuário: \n {trabalho}")])

        chain_analise = prompt_analise | llm

        analise = chain_analise.invoke({"trabalhos_exemplo": trabalhos_exemplo, "trabalho": usuario_input})
        print(analise)
        #print(llm.invoke(PROMPT_ANALISE_TRABALHO).content)
