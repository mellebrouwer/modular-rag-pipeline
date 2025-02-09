from uuid import uuid4

from langchain.docstore.document import Document as LCDocument
from langchain.embeddings.base import Embeddings
from langchain_chroma import Chroma

from src.components.vector_stores.base_vector_store import BaseVectorStore
from src.models import Document


class LcChromaStore(BaseVectorStore):
    def __init__(
        self,
        embedding_model: Embeddings,
        persist_directory: str = "db/chroma_db",
        collection_name: str = "default_collection",
    ):
        """
        Args:
            embedding_model (Embeddings): LangChain Embeddings instance.
            persist_directory (str): Where Chroma stores its database.
            collection_name (str): Unique collection name for your data in Chroma.
        """
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self._chroma = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model,
        )

        try:
            self._chroma.reset_collection()
            print("Reset existing collection successful.")
        except ValueError:
            pass

    def add_documents(self, documents: list[Document]):
        """Convert custom Document to LangChain Document and add to Chroma."""
        lc_docs = []
        for doc in documents:
            lc_docs.append(LCDocument(page_content=doc.content, metadata=doc.meta_data))
        uuids = [str(uuid4()) for _ in range(len(documents))]
        self._chroma.add_documents(documents=lc_docs, ids=uuids)

    def get_index(self):
        """Return the Chroma instance so retrievers can query it."""
        return self._chroma
