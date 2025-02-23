from src.components.query_transformers.base_query_transformer import (
    BaseQueryTransformer,
)
from src.models import Query


class SingleQuery(BaseQueryTransformer):
    def __init__(self):
        pass

    def run(self, queries: list[Query]) -> list[Query]:
        new_queries = []
        for query in queries:
            new_queries.append(query) 
        return new_queries
