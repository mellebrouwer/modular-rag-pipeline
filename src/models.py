from enum import Enum
from pprint import pformat
from typing import Any, Optional

from pydantic import BaseModel


class Query(BaseModel):
    text: str


class Document(BaseModel):
    content: str
    meta_data: dict[str, str] = {}


class Prompt(BaseModel):
    system_message: Optional[str] = None
    query_text: str = ""
    context: Optional[str] = None


class Destination(Enum):
    RETRIEVER = "retriever"
    WEB_SEARCH = "web_search"
    RELATIONAL_DB = "relational_db"


class Route(BaseModel):
    destination: Destination
    queries: list[Query]


class RoutingTable(BaseModel):
    routes: dict[Destination, list[Query]]

    def get_queries_for(self, destination: Destination) -> list[Query]:
        return self.routes.get(destination, [])


class Response(BaseModel):
    content: str = ""
    token_count: int = 0


class Data(BaseModel):
    documents_loaded: list[Document] = []
    documents_chunked: list[Document] = []
    documents_retrieved: list[Document] = []
    index: Any = None  # Allow for any as the user is responsible for matching the index / retriever
    queries: list[Query] = []
    routing_table: RoutingTable = RoutingTable(routes={})
    prompt: Prompt = Prompt()
    response: Response = Response()
    actual_answer: Optional[str] = None
    evaluation: Optional[bool] = None

    def sum_token_count(self) -> int:
        """
        Calculate the total token count across all relevant members in Data.
        """
        total_tokens = 0

        # Sum token counts from the response
        total_tokens += self.response.token_count

        # TODO: Implement token_count from other parts of the pipeline

        return total_tokens

    def __str__(self):
        return pformat(
            {
                "documents_retrieved": self.documents_retrieved,
                "index": self.index,
                "queries": self.queries,
                "routing_table": self.routing_table,
                "prompt": self.prompt,
                "response": self.response,
                "actual_answer": self.actual_answer,
                "evaluation": self.evaluation,
            }
        )
