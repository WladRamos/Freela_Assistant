import os
import requests
from dotenv import load_dotenv, set_key, find_dotenv
from datetime import datetime, timezone

class Guru:
    def __init__(self):
        # Localiza e carrega as variáveis do arquivo .env
        self.env_file = find_dotenv()
        load_dotenv(self.env_file)

        self.__load_tokens()

    def __load_tokens(self) -> None:
        # Carrega os tokens do arquivo .env
        load_dotenv(self.env_file, override=True)
        self.access_token = os.getenv('GURU_ACCESS_TOKEN')
        self.refresh_token = os.getenv('GURU_REFRESH_TOKEN')
        self.client_id = os.getenv('GURU_CLIENT_ID')
        self.client_secret = os.getenv('GURU_CLIENT_SECRET')

    def __refresh_access_token(self) -> None:
        self.__load_tokens()
        print("refresh token atual: ", self.refresh_token)
        url = "https://www.guru.com/api/v1/oauth/token/access"
        payload = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'grant_type': 'refresh_token'
        }

        # Faz a requisição POST para obter um novo access token
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get('access_token')
            new_refresh_token = data.get('refresh_token')

            if new_access_token and new_refresh_token:
                # Atualiza os valores no arquivo .env
                set_key(self.env_file, 'GURU_ACCESS_TOKEN', new_access_token)
                set_key(self.env_file, 'GURU_REFRESH_TOKEN', new_refresh_token)
                
                # Atualiza os tokens na instância após atualização no .env
                self.__load_tokens()

                print('Tokens atualizados com sucesso (usando refresh token).')
            else:
                print("Erro: Resposta não contém 'access_token' ou 'refresh_token'.")
            
        elif response.status_code in (400, 401):
            # Possível que o refresh token expirou
            print("Status: ", response.status_code)
            erro = response.json()
            print("erro")
            print(erro)
            print("Refresh token expirado. Tentando obter novo access token usando client credentials.")
            self.__get_access_token_with_client_credentials()

        else:
            print(f"Erro ao atualizar access token: {response.status_code}")
            print(response.text)


    def __get_access_token_with_client_credentials(self) -> None:

        self.__load_tokens()


        url = "https://www.guru.com/api/v1/oauth/token/access"
        payload = {
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'client_id': self.client_id
        }

        # Faz a requisição PUT para obter um novo access token
        response = requests.put(url, data=payload)

        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get('access_token')
            new_refresh_token = data.get('refresh_token')

            if new_access_token and new_refresh_token:
                # Atualiza os valores no arquivo .env
                set_key(self.env_file, 'GURU_ACCESS_TOKEN', new_access_token)
                set_key(self.env_file, 'GURU_REFRESH_TOKEN', new_refresh_token)
                
                # Atualiza os tokens na instância após atualização no .env
                self.__load_tokens()  

                print("refresh token novo: ", self.refresh_token)
                print('Tokens atualizados com sucesso (usando client credentials).')
            else:
                print("Erro: Resposta não contém 'access_token' ou 'refresh_token'.")
        else:
            print(f"Erro ao obter access token usando client credentials: {response.status_code}")
            print(response.text)

    def __get_access_token(self) -> None:
        # Tenta primeiro atualizar o token usando o refresh token
        if self.refresh_token:
            self.__refresh_access_token()

    def get_jobs(self, budget_type: str = "all", country: str = "all", period: str = "all", page_number: int = 1, page_size: int = 30) -> list[dict]:
   
        url = f"https://www.guru.com/api/v1/search/job?category=programming-development&budgetType={budget_type}&country={country}&period={period}&pagenumber={page_number}&pagesize={page_size}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers)

        # Verifica se a resposta está autorizada
        if response.status_code == 401:
            print("Token expirado. Tentando atualizar o token e refazer a requisição...")
            self.__get_access_token()  # Atualiza o token de acesso
            headers["Authorization"] = f"Bearer {self.access_token}"  # Atualiza o cabeçalho com o novo token
            response = requests.get(url, headers=headers)  # Segunda tentativa com o novo token


        if response.status_code == 200:

            data = response.json().get("Results", [])
            jobs = []

            for job in data:
                job_id = job.get('JobId')

                job_details_response = requests.get(f'https://www.guru.com/api/v1/jobs/{job_id}/summary', headers=headers)
                
                job_details = None
                if job_details_response.status_code == 401:
                    print("Token expirado. Tentando atualizar o token e refazer a requisição...")
                    self.__get_access_token()  # Atualiza o token de acesso
                    headers["Authorization"] = f"Bearer {self.access_token}"  # Atualiza o cabeçalho com o novo token
                    job_details_response = requests.get(f'https://www.guru.com/api/v1/jobs/{job_id}/summary', headers=headers)

                if job_details_response.status_code == 200:
                    job_details = job_details_response.json().get('Data')

                job_info = {
                    "title": job.get("JobTitle"),
                    "description": job.get("JobDescription"),
                    "category": job.get("JobCategory"),
                    "subcategory": job.get("JobSubCategory"),
                    "skills": job.get("Skills", []),
                    "budget_type": job.get("BudgetType"),
                    "link": f"https://www.guru.com/work/detail/{job_id}",
                    "published": self.format_timestamp_to_gmt(job.get('DatePosted')),
                    "budget_minimum": job_details.get("Budget").get("MinRate") if job_details else None,
                    "budget_maximum": job_details.get("Budget").get("MaxRate") if job_details else None
                }
                jobs.append(job_info)

            return jobs
        elif response.status_code == 204:
            print("Nenhum conteúdo encontrado.")
            return []
        elif response.status_code == 401:
            print("Acesso não autorizado. Verifique seu token.")
            return []
        elif response.status_code == 404:
            print("Endpoint não encontrado.")
            return []
        else:
            print(f"Erro desconhecido: {response.status_code}")
            print(response.text)
            return []
        
    def format_timestamp_to_gmt(self, timestamp_ms):
        # Converte o timestamp de milissegundos para segundos
        timestamp_s = int(timestamp_ms) / 1000
        
        # Converte para UTC com reconhecimento de fuso horário
        date_str = datetime.fromtimestamp(timestamp_s, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        return date_str