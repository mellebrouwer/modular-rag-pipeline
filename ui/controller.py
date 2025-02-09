import asyncio
import importlib
import inspect
import os
import re
import time

import yaml

from component_config import ComponentConfig
from src.models import Data, Query
from src.pipeline import Pipeline


class Controller:
    def __init__(self):
        self.base_path = "src/components"
        self.resources_path = "src/resources"

    def get_component_implementations(self, component_name: str) -> list[str]:
        """
        Introspect src/components/{component_type}s folder to get valid classes.
        Omits __init__ and base_* files, then extracts class names.
        """
        folder_path = os.path.join(self.base_path, f"{component_name}s")
        if not os.path.isdir(folder_path):
            return []

        names = []
        for fname in os.listdir(folder_path):
            if fname.startswith("__") or fname.startswith("base_") or not fname.endswith(".py"):
                continue
            class_name = self._find_class_name_in_file(os.path.join(folder_path, fname))
            if class_name:
                names.append(class_name)
        return names

    def get_constructor_params(self, component: str, implementation: str) -> dict:
        """
        Dynamically inspect the constructor to determine required params and types.
        Return a dict: { 'param_name': 'param_type' }.
        """
        snake_name = self._camel_to_snake(implementation)
        module_name = f"src.components.{component}s.{snake_name}"
        mod = importlib.import_module(module_name)
        cls = getattr(mod, implementation)
        sig = inspect.signature(cls.__init__)
        params = {}
        for p_name, p in sig.parameters.items():
            if p_name != "self":
                params[p_name] = p.annotation
        return params

    @staticmethod
    def get_resource_options(resource_key: str) -> list[str]:
        """
        Dynamically parse the corresponding Python file in src/resources
        to gather resource names, ignoring modules, classes, or private names.
        """
        module_name = f"src.resources.{resource_key}s"
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            return []

        resource_names = []
        for name, value in mod.__dict__.items():
            # Ignore private names, modules, classes
            if name.startswith("_"):
                continue
            if inspect.ismodule(value) or inspect.isclass(value):
                continue
            # If you only want certain object types, add more checks here.
            resource_names.append(name)

        return resource_names

    async def run_evaluation(
            self,
            index_config: list[ComponentConfig],
            retrieval_config: list[ComponentConfig],
            qa_file_path: str
    ) -> dict:
        """
        1) Builds a pipeline with indexing+retrieval config.
        2) Runs indexing once (async).
        3) Loads Q&A pairs from qa_file_path.
        4) For each Q, runs retrieval in parallel, using data.actual_answer & data.evaluation.
        5) Returns a summary dict with correctness, latencies, token usage, etc.
        """

        # 1) Build pipeline with combined config
        config_dict = {
            "pipeline_indexing": [component.to_dict() for component in index_config],
            "pipeline_retrieval": [component.to_dict() for component in retrieval_config]
        }
        print(config_dict)

        pipeline = Pipeline(config=config_dict)

        # 2) Run indexing once in a thread
        start_time = time.perf_counter()
        index_data = await asyncio.to_thread(pipeline.run_indexing, Data())
        indexing_latency = time.perf_counter() - start_time

        # 3) Load Q&A pairs from file
        qa_pairs = self._load_qa_file(qa_file_path)
        if not qa_pairs:
            return {
                "correct_count": 0,
                "incorrect_count": 0,
                "message": f"No Q&A pairs found in {qa_file_path}",
            }

        # 4) For each Q, run retrieval in parallel
        retrieval_latencies = []
        correct_count = 0
        incorrect_count = 0
        total_tokens = 0

        # Helper for concurrency
        async def process_qa(question_text: str, actual_answer: str):
            t0 = time.perf_counter()
            # Use existing index, so we pass index_data.index
            new_data = Data(queries=[Query(text=question_text)], index=index_data.index, actual_answer=actual_answer)

            # Run retrieval in a thread
            retrieval_data = await asyncio.to_thread(pipeline.run_retrieval, new_data)
            elapsed = time.perf_counter() - t0

            # Extract results
            pipeline_answer = retrieval_data.response.content
            is_correct = retrieval_data.evaluation
            token_used = retrieval_data.sum_token_count()

            return is_correct, elapsed, token_used, question_text, pipeline_answer

        tasks = []
        for qa in qa_pairs:
            # Suppose we only need the question from each QA
            question_text = qa["question"]
            actual_answer = qa["answer"]
            tasks.append(process_qa(question_text, actual_answer))

        # Wait for all tasks
        results = await asyncio.gather(*tasks)

        # Collate results
        for is_correct, elapsed, token_used, question_text, pipeline_answer in results:
            retrieval_latencies.append(elapsed)
            total_tokens += token_used
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1

        avg_retrieval_latency = 0
        if retrieval_latencies:
            avg_retrieval_latency = sum(retrieval_latencies) / len(retrieval_latencies)

        return {
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "indexing_latency": indexing_latency,
            "avg_retrieval_latency": avg_retrieval_latency,
            "total_tokens": total_tokens,
            "message": f"Ran {len(qa_pairs)} Q&A pairs."
        }

    @staticmethod
    def run_indexing_pipeline(config: list[ComponentConfig]) -> dict:
        """
        Runs the indexing pipeline using the updated_config (list of step dicts).
        Returns a dict with latency, token_count, and a message.
        """
        config_dict = {"pipeline_indexing": [component.to_dict() for component in config]}
        pipeline = Pipeline(config=config_dict)

        data = Data()
        start_time = time.perf_counter()
        indexed_data = pipeline.run_indexing(data)
        latency = time.perf_counter() - start_time

        # If sum_token_count is relevant at indexing stage, use it. Otherwise it might be 0.
        token_count = indexed_data.sum_token_count()

        return {
            "latency": latency,
            "token_count": token_count,
            "message": "Indexing pipeline completed successfully!"

        }

    @staticmethod
    def run_retrieval_pipeline(config: list[ComponentConfig], query_text: str, actual_answer: str) -> dict:
        """
        Runs the retrieval pipeline using updated_config and the user query.
        Returns a dict with latency, token_count, and the final answer.
        """
        config_dict = {"pipeline_retrieval": config}
        pipeline = Pipeline(config=config_dict)

        data = Data(queries=[Query(text=query_text)], actual_answer=actual_answer)
        start_time = time.perf_counter()
        retrieved_data = pipeline.run_retrieval(data)
        latency = time.perf_counter() - start_time

        eval_result = retrieved_data.evaluation
        token_count = retrieved_data.sum_token_count()
        final_answer = retrieved_data.response.content or "No answer was produced by the retrieval pipeline."

        return {
            "latency": latency,
            "token_count": token_count,
            "message": final_answer,
            "evaluation": eval_result,
        }

    @staticmethod
    def load_config() -> dict:
        """Load the YAML config from 'config.yaml' in the main directory."""
        config_file = os.path.join(os.getcwd(), "config.yaml")
        if not os.path.exists(config_file):
            raise FileNotFoundError("No config.yaml file found in the current working directory.")

        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _load_qa_file(qa_file_path: str) -> list[dict]:
        """Load Q&A pairs from a YAML or JSON (here YAML) file."""
        import yaml
        if not os.path.exists(qa_file_path):
            return []
        with open(qa_file_path, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _find_class_name_in_file(file_path: str) -> str:
        """
        A simple approach to extract class name from a Python file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"class\s+([A-Z]\w+)", content)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")



