import os

from src.components.document_loaders.base_document_loader import BaseDocumentLoader
from src.models import Document


class MultiLoader(BaseDocumentLoader):
    def __init__(self, directory: str):
        """
        Args:
            directory (str): The relative directory within the `data` folder to load files from.
        """
        self.directory = directory

    def run(self) -> list[Document]:
        """Load all `.csv` files from the specified directory as raw text."""
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"Directory {self.directory} does not exist.")

        documents = []
        for filename in os.listdir(self.directory):
            if filename.endswith(".csv") or filename.endswith(".txt"):
                file_path = os.path.join(self.directory, filename)
                print(f"Loading file: {file_path}")
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    documents.append(Document(content=content, meta_data={"filename": filename}))

        return documents
