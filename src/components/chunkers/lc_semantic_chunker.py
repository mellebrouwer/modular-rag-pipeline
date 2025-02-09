from langchain.embeddings.base import Embeddings
from langchain_experimental.text_splitter import SemanticChunker

from src.components.chunkers.base_chunker import BaseChunker
from src.models import Document


class LcSemanticChunker(BaseChunker):
    """Chunks documents based on semantic similarity using LangChain's SemanticChunker."""

    def __init__(self, embedding_model: Embeddings):
        """
        Args:
            embedding_model (Embeddings): The embedding model to use for semantic similarity.
        """
        self.semantic_chunker = SemanticChunker(embedding_model)

    def run(self, documents: list[Document]) -> list[Document]:
        """Chunk documents into semantically similar parts."""
        chunked_documents = []

        for doc in documents:
            langchain_docs = self.semantic_chunker.create_documents([doc.content])
            for idx, lc_doc in enumerate(langchain_docs):
                chunk_metadata = doc.meta_data.copy()
                chunk_metadata["chunk"] = (
                    f"{chunk_metadata.get('filename', 'unknown')} - chunk {idx + 1}"
                )
                chunked_documents.append(
                    Document(content=lc_doc.page_content, meta_data=chunk_metadata)
                )

        return chunked_documents
