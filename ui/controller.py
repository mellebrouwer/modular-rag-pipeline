import asyncio
import importlib
import inspect
import os
import time

from component_config import ComponentConfig
from src.models import Data, Query
from src.pipeline import Pipeline
from ui.utilities import camel_to_snake, find_class_name_in_file, load_qa_file


class Controller:
    """
    Controller class to manage pipeline operations, component introspection, and resource loading for Streamlit UI

    Responsibilities:
    - Dynamically introspect components and their implementations.
    - Load configurations and Q&A files.
    - Run indexing and retrieval pipelines.
    - Evaluate pipeline results using Q&A pairs.
    """
    def __init__(self):
        self.component_path = "src/components"
        self.resources_path = "src/resources"

    def get_component_implementations(self, component_name: str) -> list[str]:
        """
        Get all valid implementations of a given component type.

        Args:
            component_name (str): The name of the component type.

        Returns:
            list[str]: A list of class names representing the available implementations.
        """
        module_name = os.path.join(self.component_path, f"{component_name}s")
        if not os.path.isdir(module_name):
            return []

        names = []
        for fname in os.listdir(module_name):
            if fname.startswith("__") or fname.startswith("base_") or not fname.endswith(".py"):
                continue
            class_name = find_class_name_in_file(os.path.join(module_name, fname))
            if class_name:
                names.append(class_name)
        return names

    def get_resource_implementations(self, resource_key: str) -> list[str]:
        """
        Retrieve available resource options for a given key.

        Args:
            resource_key (str): The key representing the resource type (e.g., "embedding_model").

        Returns:
            list[str]: A list of available resource names.
        """
        module_name = os.path.join(self.resources_path, f"{resource_key}s")
        module_name = module_name.replace("/", ".")
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

    def get_constructor_params(self, component: str, implementation: str) -> dict:
        """
        Dynamically inspect the constructor to determine required params and types.
        Return a dict: { 'param_name': 'param_type' }.
        """
        snake_name = camel_to_snake(implementation)
        module_name = os.path.join(self.component_path, f"{component}s.{snake_name}")
        module_name = module_name.replace("/", ".")
        mod = importlib.import_module(module_name)
        cls = getattr(mod, implementation)
        sig = inspect.signature(cls.__init__)
        params = {}
        for p_name, p in sig.parameters.items():
            if p_name != "self":
                params[p_name] = p.annotation
        return params

    @staticmethod
    async def run_evaluation(
            index_config: list[ComponentConfig],
            retrieval_config: list[ComponentConfig],
            qa_file_path: str
    ) -> dict:
        """
        Run the evaluation pipeline with indexing and retrieval configurations.

        Args:
            index_config (list[ComponentConfig]): Indexing phase configuration.
            retrieval_config (list[ComponentConfig]): Retrieval phase configuration.
            qa_file_path (str): Path to the Q&A YAML file.

        Returns:
            dict: Summary of evaluation results including correctness, latencies, and token usage.
        """
        # 1) Build pipeline with combined config
        config_dict = {
            "pipeline_indexing": [component.to_dict() for component in index_config],
            "pipeline_retrieval": [component.to_dict() for component in retrieval_config]
        }

        pipeline = Pipeline(config=config_dict)

        # 2) Run indexing once in a thread
        start_time = time.perf_counter()
        index_data = await asyncio.to_thread(pipeline.run_indexing, Data())
        indexing_latency = time.perf_counter() - start_time

        # 3) Load Q&A pairs from file
        qa_pairs = load_qa_file(qa_file_path)
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
