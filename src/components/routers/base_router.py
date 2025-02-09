from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Query, RoutingTable


class BaseRouter(PipelineComponent):
    def validate_input_data(self, data: Data):
        if not isinstance(data.queries, list):
            raise ValueError(f"Router expected a list[Query], got {type(data.queries).__name__}")
        if not data.queries:
            raise ValueError("Router expected a non-empty list[Query], got an empty list")

    def extract_input(self, data: Data) -> list[Query]:
        return data.queries

    def update_data(self, data: Data, result: RoutingTable):
        data.routing_table = result

    @abstractmethod
    def run(self, queries: list[Query]) -> RoutingTable:
        pass
