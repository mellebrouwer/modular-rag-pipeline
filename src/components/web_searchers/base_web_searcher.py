from abc import abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Destination, Document, Query, RoutingTable


class BaseWebSearcher(PipelineComponent):
    def validate_input_data(self, data: Data):
        if not hasattr(data, "routing_table") or not isinstance(data.routing_table, RoutingTable):
            raise ValueError("WebSearch requires a valid RoutingTable in the data.")
        queries = self.get_queries(data)
        if not isinstance(queries, list):
            raise ValueError(f"WebSearch expected a list[Query], got {type(queries).__name__}")
        if not queries:
            raise ValueError("WebSearch expected a non-empty list[Query], got an empty list")
        if not isinstance(queries[0], Query):
            raise ValueError(f"WebSearch expected a list[Query], got {type(queries[0]).__name__}")

    def extract_input(self, data: Data) -> list[Query]:
        return self.get_queries(data)

    def update_data(self, data: Data, result: list[Document]):
        data.documents_retrieved.extend(result)

    @staticmethod
    def get_queries(data: Data) -> list[Query]:
        return data.routing_table.get_queries_for(Destination.WEB_SEARCH)

    @abstractmethod
    def run(self, queries: list[Query]) -> list[Document]:
        pass
