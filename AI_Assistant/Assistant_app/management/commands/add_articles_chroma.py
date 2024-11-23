from django.core.management.base import BaseCommand
import chromadb
from pathlib import Path


class Command(BaseCommand):
    help = 'Adiciona dados de URLs ao ChromaDB'

    def handle(self, *args, **options):
        # Caminho do diretório base
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Caminho do arquivo urls.txt
        caminho_urls = base_dir / 'dados/urls.txt'
        
        # Caminho do PersistentClient
        caminho_persistent_client = base_dir.parent
        
        # Lê o arquivo urls.txt
        try:
            with open(caminho_urls, 'r') as file:
                urls = file.read().splitlines()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Arquivo {caminho_urls} não encontrado."))
            return

        # Conexão com o Chroma DB
        client = chromadb.PersistentClient(path=str(caminho_persistent_client))
        collection = client.create_collection("Base_de_Artigos")

        # Processamento das URLs
        for i, url in enumerate(urls):
            try:
                # Extrai o título da URL
                if url.endswith('/'):
                    titulo = url.rstrip('/').split('/')[-1]
                else:
                    titulo = url.split('/')[-1]
                titulo = titulo.replace('-', ' ')
                print("URL: ", url)
                print("Titulo: ", titulo)

                # Document e metadata
                document = titulo
                metadata = {'title': titulo, 'url': url}

                # Adiciona ao Chroma DB
                collection.add(
                    documents=[document],
                    metadatas=[metadata],
                    ids=[str(i)]
                )
                self.stdout.write(self.style.SUCCESS(f"URL {i} adicionada com sucesso: {url}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao adicionar a URL {i}: {url} - {e}"))

        self.stdout.write(self.style.SUCCESS("Dados inseridos com sucesso no Chroma DB!"))
