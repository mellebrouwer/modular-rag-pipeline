from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.components.answer_generators.base_answer_generator import BaseAnswerGenerator
from src.models import Prompt, Response


class LcAnswerGenerator(BaseAnswerGenerator):
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def run(self, prompt: Prompt) -> Response:
        system_message = SystemMessage("You are a helpful assistant.")  # Default system message
        if prompt.system_message:
            system_message = SystemMessage(prompt.system_message)
        query = HumanMessage(f"Query: {prompt.query_text} \n\nContext: {prompt.context}")
        result = self.llm.invoke([system_message, query])
        content = str(result.content)
        token_count = result.usage_metadata["total_tokens"]
        return Response(content=content, token_count=token_count)
