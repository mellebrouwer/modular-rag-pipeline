from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Prompt, Response


class BaseAnswerGenerator(PipelineComponent):
    """Base class for generating answers with an llm."""

    def validate_input_data(self, data: Data):
        if not isinstance(data.prompt, Prompt):
            raise ValueError(f"AnswerGenerator expected a Prompt, got {type(data.prompt).__name__}")
        if not data.prompt.query_text:
            raise ValueError("Prompt query must not be empty")
        if not data.prompt.context:
            raise ValueError("Prompt context must not be empty")

    def extract_input(self, data: Data) -> Prompt:
        return data.prompt

    def update_data(self, data: Data, result: Response):
        data.response = result

    @abstractmethod
    def run(self, prompt: Prompt) -> Response:
        pass
