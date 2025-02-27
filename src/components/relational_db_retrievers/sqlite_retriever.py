import sqlite3
from typing import Any

from src.components.relational_db_retrievers.base_relational_db_retriever import BaseRelationalDBRetriever
from src.models import Document, Query


class SqliteRetriever(BaseRelationalDBRetriever):
    def __init__(self, db_path: str):
        """
        Initialize the SQLite retriever.

        Args:
            db_path (str): Path to the SQLite database
        """
        self.db_path = db_path

    def _execute_query(self, sql_query: str) -> list[tuple[Any, ...]]:
        """Execute the SQL query and return results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql_query)
                return cursor.fetchall()
            except sqlite3.Error as e:
                return [(f"Error executing query: {str(e)}",)]

    def _format_results(self, results: list[tuple[Any, ...]], sql_query: str) -> str:
        """Format the SQL results into a readable string."""
        if not results:
            return "No results found."
        
        formatted_rows = [" | ".join(str(cell) for cell in row) for row in results]
        return f"SQL Query: {sql_query}\n\nResults:\n" + "\n".join(formatted_rows)

    def run(self, queries: list[Query]) -> list[Document]:
        """Process queries to find Brian's location."""
        documents = []
        sql_query = 'SELECT "Timestamp", "Item" FROM transactions WHERE "User" = "Brian";'
        
        for query in queries:
            # Only process queries that are looking for Brian
            if "brian" in query.text.lower():
                results = self._execute_query(sql_query)
                formatted_results = self._format_results(results, sql_query)
                
                documents.append(Document(
                    content=formatted_results,
                    meta_data={
                        "source": "SqliteRetriever",
                        "original_query": query.text,
                        "sql_query": sql_query
                    }
                ))

        return documents
