from Assistant_app.services.remotive import Remotive
from Assistant_app.services.freelancermap import Freelancermap
from Assistant_app.services.freelancercom import Freelancercom
from Assistant_app.services.guru import Guru
from bs4 import BeautifulSoup
import re

class JobFetcher:
    def __init__(self, filters: list[str] = []) -> None:
        self.__all_jobs_str = ""
        self.filters = filters
        self.__fetch_jobs()
        
    
    def __fetch_jobs(self) -> None:

        flmap_jobs = self.__clean_job_descriptions(Freelancermap.parse_feeds())
        if len(self.filters) > 0:
            flmap_jobs = self.__job_filter(flmap_jobs, self.filters)
        self.__all_jobs_str += self.write_jobs_str(flmap_jobs, "Freelancermap.com")

        remotive_jobs = self.__clean_job_descriptions(Remotive.parse_feeds())
        if len(self.filters) > 0:
            remotive_jobs = self.__job_filter(remotive_jobs, self.filters)
        self.__all_jobs_str += self.write_jobs_str(remotive_jobs, "Remotive.com")

        freelcom = Freelancercom(query=' '.join(self.filters))
        freelcom_jobs = freelcom.get_jobs()
        if len(self.filters) > 0:
            freelcom_jobs = self.__job_filter(freelcom_jobs, self.filters)
        self.__all_jobs_str += self.write_jobs_str(freelcom_jobs, "Freelancer.com")

        guru = Guru()
        guru_jobs = guru.get_jobs()
        if len(self.filters) > 0:
            guru_jobs = self.__job_filter(guru_jobs, self.filters)
        self.__all_jobs_str += self.write_jobs_str(guru_jobs, "Guru.com")
        


    
    def __job_filter(self, jobs: list[dict], filters: list[str]) -> list[dict]:
        filtered_jobs = []
        
        for job in jobs:
            job_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')} {job.get('category', '')} {job.get('subcategory', '')} {job.get('skills', '')}".lower()
            
            for filter_word in filters:
                filter_word_lower = filter_word.lower()
                
                if f" {filter_word_lower} " in f" {job_text} ":
                    filtered_jobs.append(job)
                    break
                    
        return filtered_jobs
    
    def __clean_job_descriptions(self, jobs: list[dict]) -> list[dict]:
        for job in jobs:
            if 'description' in job and job['description']:
                # Usar BeautifulSoup para limpar a descrição
                soup = BeautifulSoup(job['description'], "html.parser")
                clean_text = soup.get_text(separator=" ").strip()
                
                # Remover espaços em branco excessivos e caracteres especiais
                clean_text = re.sub(r'\s+', ' ', clean_text)  # Substitui múltiplos espaços por um único
                clean_text = re.sub(r'[\n\r]+', ' ', clean_text)  # Remove quebras de linha
                clean_text = re.sub(r'\xa0', ' ', clean_text)  # Remove espaços não quebráveis (&nbsp;)
                
                # Atualizar a descrição no dicionário
                job['description'] = clean_text
        
        return jobs
    
    
    def write_jobs_str(self, jobs: list[dict], website: str) -> str:
        # Inicia a string com o nome do website
        job_str = f"Website: {website}\n"
        job_str += "=" * (9 + len(website)) + "\n\n"  # Linha de separação
        
        # Itera sobre os trabalhos e formata cada um deles
        for job in jobs:
            title = job.get('title')
            company = job.get('company')
            job_type = job.get('job_type')
            description = job.get('description')
            category = job.get('category')
            subcategory = job.get('subcategory')
            skills = job.get('skills')
            link = job.get('link')
            published = job.get('published')
            budget_type = job.get('budget_type')
            min_budget = job.get("budget_minimum")
            max_budget = job.get("budget_maximum")

            # Monta a string formatada para o trabalho atual
            if title is not None:
                job_str += f"Title: {title}\n"
            if company is not None:
                job_str += f"Company: {company}\n"
            if job_type is not None:
                job_str += f"Job Type: {job_type}\n"
            if category is not None:
                job_str += f"Category: {category}\n"
            if subcategory is not None:
                job_str += f"Subcategory: {subcategory}\n"
            if skills is not None:
                job_str += f"Skills: {skills}\n"
            if published is not None:
                job_str += f"Published: {published}\n"
            if budget_type is not None :
                job_str += f"Budget Type: {budget_type}\n"
            if min_budget is not None and min_budget != 0:
                job_str += f"Minimum Budget: {min_budget}\n"
            if max_budget is not None and max_budget != 0:
                job_str += f"Maximum Budget: {max_budget}\n"
            if link is not None:
                job_str += f"Link: {link}\n"
            if description is not None:
                job_str += "Description:\n"
                job_str += f"{description}\n"
            job_str += "-" * 40 + "\n\n"
    
        return job_str
    
    def get_jobs_str(self):
        return self.__all_jobs_str

if __name__ == "__main__":
    jobs = JobFetcher(filters=["python", "developer"])
    print(jobs.get_jobs_str())