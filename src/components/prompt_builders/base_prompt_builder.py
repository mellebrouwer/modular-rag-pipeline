from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Document, Prompt, Query


class BasePromptBuilder(PipelineComponent):
    def validate_input_data(self, data: Data):
        if not isinstance(data.documents_retrieved, list):
            raise ValueError(
                f"PromptBuilder expected a list[Document], "
                f"got {type(data.documents_retrieved).__name__}"
            )
        if not data.documents_retrieved:
            raise ValueError("PromptBuilder expected a non-empty list[Document], got an empty list")
        if not isinstance(data.documents_retrieved[0], Document):
            raise ValueError(
                f"PromptBuilder expected a list[Document], "
                f"got {type(data.documents_retrieved[0]).__name__}"
            )

    def extract_input(self, data: Data) -> tuple[list[Document], list[Query]]:
        return data.documents_retrieved, data.queries

    def update_data(self, data: Data, result: Prompt):
        data.prompt = result

    @abstractmethod
    def run(self, documents: list[Document], queries: list[Query]) -> Prompt:
        pass
