from src.components.evaluators.base_evaluator import BaseEvaluator
from src.models import Query, Response


class NoEvaluator(BaseEvaluator):
    def __init__(self):
        pass

    def run(self, response: Response, query: Query, actual_answer: str) -> bool:
        """No operation evaluator. Always returns False."""
        return False
