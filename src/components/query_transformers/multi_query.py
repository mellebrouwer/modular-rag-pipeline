from src.components.query_transformers.base_query_transformer import (
    BaseQueryTransformer,
)
from src.models import Query


class MultiQuery(BaseQueryTransformer):
    def __init__(self):
        pass

    def run(self, queries: list[Query]) -> list[Query]:
        # Example logic: Create some queries for websearch
        new_queries = []
        for query in queries:
            new_queries.append(query)  # Original query
            new_queries.append(Query(text=f"Search the web for: {query.text}"))
            new_queries.append(Query(text=f"Search the relational database for: {query.text}"))
        return new_queries
