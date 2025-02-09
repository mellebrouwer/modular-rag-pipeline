from src.components.relational_db_retrievers.base_relational_db_retriever import (
    BaseRelationalDBRetriever,
)
from src.models import Document, Query


class MockRelationalDbRetriever(BaseRelationalDBRetriever):
    def run(self, queries: list[Query]) -> list[Document]:
        # Mock implementation of a relational database retrieval
        documents = []
        for query in queries:
            documents.append(
                Document(
                    content=f"Mock database results for: {query.text}",
                    meta_data={"source": "BasicRelationalDBRetriever"},
                )
            )
        return documents
