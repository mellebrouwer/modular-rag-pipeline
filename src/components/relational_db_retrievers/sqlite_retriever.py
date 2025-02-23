import sqlite3
from typing import Any
from langchain.chat_models.base import BaseChatModel

from src.components.relational_db_retrievers.base_relational_db_retriever import BaseRelationalDBRetriever
from src.models import Document, Query


class SqliteRetriever(BaseRelationalDBRetriever):
    def __init__(self, llm: BaseChatModel, prompt: str, db_path: str):
        """
        Initialize the SQLite retriever.

        Args:
            llm (BaseChatModel): LLM for converting natural language to SQL
            prompt (str): System prompt for SQL generation
            db_path (str): Path to the SQLite database
        """
        self.llm = llm
        self.prompt = prompt
        self.db_path = db_path

    def _get_table_schema(self) -> str:
        """Get the schema of all tables in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_info = [f"{col[1]} ({col[2]})" for col in columns]
                schema.append(f"Table {table_name}: {', '.join(column_info)}")
            
            return "\n".join(schema)

    def _generate_sql_query(self, query: str, schema: str) -> str:
        """Generate SQL query using the LLM."""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": f"Schema:\n{schema}\n\nQuery: {query}"}
        ]
        response = self.llm.invoke(messages)
        return response.content

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
        
        # Convert all results to strings and join with newlines
        formatted_rows = [" | ".join(str(cell) for cell in row) for row in results]
        return f"SQL Query: {sql_query}\n\nResults:\n" + "\n".join(formatted_rows)

    def run(self, queries: list[Query]) -> list[Document]:
        """
        Process natural language queries into SQL, execute them, and return results.

        Args:
            queries (list[Query]): List of natural language queries

        Returns:
            list[Document]: List containing a single document with the query results
        """
        documents = []
        schema = self._get_table_schema()

        for query in queries:
            sql_query = self._generate_sql_query(query.text, schema)
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
