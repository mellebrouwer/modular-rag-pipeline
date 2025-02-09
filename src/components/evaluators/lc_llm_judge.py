from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.components.evaluators.base_evaluator import BaseEvaluator
from src.models import Query, Response


class LcLlmJudge(BaseEvaluator):
    def __init__(self, llm: BaseChatModel, prompt: str):
        self.llm = llm
        self.prompt = prompt

    def run(self, response: Response, query: Query, actual_answer: str) -> bool:
        # Prepare system and human messages for the LLM
        system_message = SystemMessage(content=self.prompt)
        human_message = HumanMessage(
            content=(
                f"Question: {query.text}\n\n"
                f"Reference Answer: {actual_answer}\n\n"
                f"Pipeline Answer: {response.content}\n\n"
                f"Is the Pipeline Answer correct? Reply with 'TRUE' or 'FALSE'."
            )
        )

        # Get the LLM's judgment
        result = self.llm.invoke([system_message, human_message])
        judgment = str(result.content).strip().upper()

        # Interpret the judgment as boolean
        if judgment == "TRUE":
            return True
        elif judgment == "FALSE":
            return False
        else:
            raise ValueError(f"Unexpected judgment from LLM: {judgment}")
