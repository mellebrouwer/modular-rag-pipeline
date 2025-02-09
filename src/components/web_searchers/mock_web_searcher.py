from src.components.web_searchers.base_web_searcher import BaseWebSearcher
from src.models import Document, Query


class MockWebSearcher(BaseWebSearcher):
    def run(self, queries: list[Query]) -> list[Document]:
        # Mock implementation of a web search
        documents = []
        for query in queries:
            documents.append(
                Document(
                    content=f"Mock web search results for: {query.text}",
                    meta_data={"source": "BasicWebSearch"},
                )
            )
        return documents
