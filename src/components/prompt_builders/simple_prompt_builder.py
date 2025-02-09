from src.components.prompt_builders.base_prompt_builder import BasePromptBuilder
from src.models import Document, Prompt, Query


class SimplePromptBuilder(BasePromptBuilder):
    def __init__(self, prompt: str):
        self.system_message = prompt

    def run(self, documents: list[Document], queries: list[Query]) -> Prompt:
        context = "\n\n".join(str(doc) for doc in documents)
        return Prompt(
            system_message=self.system_message, query_text=queries[0].text, context=context
        )
