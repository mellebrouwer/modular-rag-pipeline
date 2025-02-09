from abc import ABC, abstractmethod
from typing import Any

from src.components.base_component import PipelineComponent
from src.models import Data, Document


class BaseVectorStore(PipelineComponent, ABC):
    """Base class for vector stores."""

    def validate_input_data(self, data: Data):
        if not isinstance(data.documents_loaded, list):
            raise ValueError(
                f"VectorStore expected a list[Document], "
                f"got {type(data.documents_loaded).__name__}"
            )
        if not data.documents_loaded:
            raise ValueError("VectorStore expected a non-empty list[Document], got an empty list")
        if not all(isinstance(doc, Document) for doc in data.documents_loaded):
            raise ValueError("All items in data.documents must be instances of Document")

    def extract_input(self, data: Data) -> list[Document]:
        """Extract the list of documents from the data object."""
        return data.documents_chunked

    def run(self, documents: list[Document]) -> Any:
        """
        Add documents to the store and return the underlying index.
        Subclasses may handle the final form of the 'index' (e.g., a DB handle).
        """
        self.add_documents(documents)
        return self.get_index()

    def update_data(self, data: Data, result):
        """Update the data object with the index (e.g., Chroma instance)."""
        data.index = result

    @abstractmethod
    def add_documents(self, documents: list[Document]):
        """Add documents to the vector store."""
        pass

    @abstractmethod
    def get_index(self):
        """Retrieve the vector store index object (e.g., Chroma instance)."""
        pass
