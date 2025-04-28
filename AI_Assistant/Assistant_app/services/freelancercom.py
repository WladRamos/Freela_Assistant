from freelancersdk.session import Session
from freelancersdk.resources.projects.projects import search_projects
from freelancersdk.resources.projects.exceptions import ProjectsNotFoundException
from freelancersdk.resources.projects.helpers import create_search_projects_filter
from dotenv import load_dotenv, find_dotenv
import os


class Freelancercom:
    def __init__(self, query):

        self.env_file = find_dotenv()
        load_dotenv(self.env_file)
        self.freelancer_api_key = os.getenv('FREELANCER_KEY')

        self.session = Session(oauth_token=self.freelancer_api_key)
        self.query = query
        self.projects_list = []

    def _search_projects(self):
        search_filter = create_search_projects_filter(
            sort_field='time_updated',
            or_search_query=True,
        )

        try:
            projects = search_projects(
                self.session,
                query=self.query,
                search_filter=search_filter,
                active_only=True,
                limit=30
            ).get("projects")

            # Processar e salvar os projetos em uma lista de dicionários
            for project in projects:
                
                project_info = {
                    'title': project.get("title"),
                    'link': f"https://www.freelancer.com/projects/{project.get('seo_url')}/details",
                    'description': project.get("preview_description"),
                    'job_type': project.get("type"),
                    'budget_minimum': project.get("budget").get("minimum"),
                    'budget_maximum': project.get("budget").get("maximum"),
                }
                self.projects_list.append(project_info)

        except ProjectsNotFoundException as e:
            print(f'Error message: {e.message}')
            print(f'Server response: {e.error_code}')

    def get_jobs(self):
        if not self.projects_list:  # Se ainda não fizermos a busca, faça
            self._search_projects()
        return self.projects_list

