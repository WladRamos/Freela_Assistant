from django.core.management.base import BaseCommand
import chromadb
import pandas as pd
from pathlib import Path


class Command(BaseCommand):
    help = 'Adiciona dados de trabalhos freelancer ao ChromaDB'

    def handle(self, *args, **options):

        base_dir = Path(__file__).resolve().parent.parent.parent

        caminho_csv = base_dir / 'dados/dados_3plataformas.csv'

        caminho_persistent_client = base_dir.parent

        df = pd.read_csv(caminho_csv, dtype=str)

        client = chromadb.PersistentClient(path=str(caminho_persistent_client))
        collection = client.create_collection("Base_de_Trabalhos")

        documents = df['Job Title'].tolist()
        metadatas = df.to_dict(orient='records')
        ids = df.index.astype(str).tolist()

        for i in range(len(documents)):
            try:
                collection.add(
                    documents=[documents[i]],
                    metadatas=[metadatas[i]],
                    ids=[ids[i]]
                )
                print(f"Documento {i} adicionado com sucesso.")
            except Exception as e:
                print(f"Erro ao adicionar o documento {i}: {e}")
                print(f"Documento problemático: {documents[i]}")
                print(f"Metadatas: {metadatas[i]}")
                print(f"ID: {ids[i]}")

        print("Dados inseridos com sucesso no Chroma DB!")