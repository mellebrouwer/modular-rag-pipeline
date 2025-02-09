from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Query, Response


class BaseEvaluator(PipelineComponent):
    def validate_input_data(self, data: Data):
        if not isinstance(data.response, Response):
            raise ValueError(f"Evaluator expected a Response, got {type(data.response).__name__}")
        if not isinstance(data.queries, list) or not data.queries:
            raise ValueError("Evaluator expected a non-empty list of Query objects.")
        if not data.actual_answer:
            raise ValueError("Evaluator expected an actual answer to compare against.")

    def extract_input(self, data: Data) -> tuple[Response, Query, str | None]:
        return data.response, data.queries[0], data.actual_answer

    def update_data(self, data: Data, result: bool):
        data.evaluation = result

    @abstractmethod
    def run(self, response: Response, query: Query, actual_answer: str) -> bool:
        pass
