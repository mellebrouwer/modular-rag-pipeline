from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Document


class BaseChunker(PipelineComponent):
    """Base class for chunking documents."""

    def validate_input_data(self, data: Data):
        if not isinstance(data.documents_loaded, list):
            raise ValueError(
                f"Chunker expected a list[Document], got {type(data.documents_loaded).__name__}"
            )
        if not data.documents_loaded:
            raise ValueError("Chunker expected a non-empty list[Document], got an empty list")
        if not all(isinstance(doc, Document) for doc in data.documents_loaded):
            raise ValueError("All items in data.documents must be instances of Document")

    def extract_input(self, data: Data) -> list[Document]:
        """Extract the list of documents from the data object."""
        return data.documents_loaded

    def update_data(self, data: Data, result: list[Document]):
        """Update the data object with chunked documents."""
        data.documents_chunked = result

    @abstractmethod
    def run(self, documents: list[Document]) -> list[Document]:
        pass
