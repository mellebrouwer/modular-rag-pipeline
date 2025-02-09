from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Query


class BaseQueryTransformer(PipelineComponent):
    def validate_input_data(self, data: Data):
        if not isinstance(data.queries, list):
            raise ValueError(
                f"QueryTransformer expected a list[Query], got {type(data.queries).__name__}"
            )
        if not data.queries:
            raise ValueError("QueryTransformer expected a non-empty list[Query], got an empty list")
        if not isinstance(data.queries[0], Query):
            raise ValueError(
                f"QueryTransformer expected a list[Query], got {type(data.queries[0]).__name__}"
            )

    def extract_input(self, data: Data) -> list[Query]:
        return data.queries

    def update_data(self, data: Data, result: list[Query]):
        data.queries = result

    @abstractmethod
    def run(self, queries: list[Query]) -> list[Query]:
        pass
