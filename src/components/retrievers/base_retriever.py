from abc import ABC, abstractmethod

from src.components.base_component import PipelineComponent
from src.models import Data, Destination, Document, Query, RoutingTable


class BaseRetriever(PipelineComponent, ABC):
    """
    Base class for retrieving documents from an index.
    Subclasses may implement advanced logic or simple keyword searches.
    """

    def validate_input_data(self, data: Data):
        # Ensure we have a routing table
        if not hasattr(data, "routing_table") or not isinstance(data.routing_table, RoutingTable):
            raise ValueError("Retriever requires a valid RoutingTable in the data.")

        queries = self.get_queries(data)
        if not isinstance(queries, list):
            raise ValueError(f"Retriever expected a list[Query], got {type(queries).__name__}")
        if not queries:
            raise ValueError("Retriever expected a non-empty list[Query], got an empty list")
        if not isinstance(queries[0], Query):
            raise ValueError(f"Retriever expected a list[Query], got {type(queries[0]).__name__}")

        # Ensure the index object is present
        if not hasattr(data, "index") or data.index is None:
            print("No indexer is set in the data object. Ensure your retriever loads an index.")

    def extract_input(self, data: Data):
        """
        Extract queries + index so the run method can use them.
        Return as a tuple so we can do run(*inputs).
        """
        return self.get_queries(data), data.index

    def update_data(self, data: Data, result: list[Document]):
        """Append retrieved documents to data.documents."""
        data.documents_retrieved.extend(result)

    @staticmethod
    def get_queries(data: Data) -> list[Query]:
        """Pull out RETRIEVER queries from the routing table."""
        return data.routing_table.get_queries_for(Destination.RETRIEVER)

    @abstractmethod
    def run(self, queries: list[Query], index) -> list[Document]:
        """
        Subclasses will define how to retrieve documents from the index given queries.
        'index' could be a Chroma instance, Faiss object, Pinecone object, etc.
        """
        pass
