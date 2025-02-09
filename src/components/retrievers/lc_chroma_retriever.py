from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from src.components.retrievers.base_retriever import BaseRetriever
from src.models import Document, Query


class LcChromaRetriever(BaseRetriever):
    def __init__(
        self,
        embedding_model: Embeddings,
        index_path: str = "db/chroma_db",
        collection_name: str = "default_collection",
        top_k: int = 4,
    ):
        """
        Args:
            top_k (int): How many results to fetch from similarity search.
        """
        self.top_k = top_k
        self.index_path = index_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model

    def run(self, queries: list[Query], index) -> list[Document]:
        """Perform a similarity search against the Chroma vector store."""
        documents: list[Document] = []

        if index is None:
            print("Index was not set, loading index")
            index = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.index_path,
                embedding_function=self.embedding_model,
            )

        for query in queries:
            # Use the built-in similarity_search method
            results = index.similarity_search(query.text, k=self.top_k)
            # Convert LangChain docs back to your custom Document
            for res in results:
                documents.append(Document(content=res.page_content, meta_data=res.metadata))
        return documents
