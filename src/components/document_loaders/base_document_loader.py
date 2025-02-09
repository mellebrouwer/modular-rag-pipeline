from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Document


class BaseDocumentLoader(PipelineComponent):
    """Base class for document loaders, agnostic of input file handling logic."""

    def validate_input_data(self, data: Data):
        """Document loaders don't require input from data."""
        pass

    def extract_input(self, data: Data) -> None:
        """Document loaders don't require input from data."""
        pass

    def update_data(self, data: Data, result: list[Document]):
        """Update the data object with loaded documents."""
        data.documents_loaded.extend(result)

    @abstractmethod
    def run(self) -> list[Document]:
        """Load documents from a source."""
        pass
