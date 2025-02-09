from src.components.chunkers.base_chunker import BaseChunker
from src.models import Document


class FixedSizeChunker(BaseChunker):
    """Chunks documents into parts based on a specified chunk size."""

    def __init__(self, chunk_size: int):
        """
        Args:
            chunk_size (int): Maximum number of characters per chunk.
        """
        self.chunk_size = chunk_size

    def run(self, documents: list[Document]) -> list[Document]:
        """Chunk documents into parts of specified size."""
        chunked_documents = []

        for doc in documents:
            content = doc.content
            num_chunks = (
                len(content) + self.chunk_size - 1
            ) // self.chunk_size  # Calculate total chunks

            for i in range(num_chunks):
                start_idx = i * self.chunk_size
                end_idx = min(start_idx + self.chunk_size, len(content))
                chunk_content = content[start_idx:end_idx]

                # Create a new Document for each chunk with updated metadata
                chunk_metadata = doc.meta_data.copy()
                chunk_metadata["chunk"] = (
                    f"{chunk_metadata.get('filename', 'unknown')} - chunk {i + 1}"
                )
                chunked_documents.append(Document(content=chunk_content, meta_data=chunk_metadata))

        return chunked_documents
