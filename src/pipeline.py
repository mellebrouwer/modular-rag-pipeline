import importlib
from typing import Optional

import dotenv
import yaml
from pydantic import ValidationError

from src.components.base_component import PipelineComponent
from src.models import Data, Query

dotenv.load_dotenv()


class Pipeline:
    def __init__(self, config_path: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize the pipeline with both retrieval and indexing pipelines.

        Args:
            config_path (str): Path to the YAML configuration file.
            config (dict): Configuration dictionary. If provided, it overrides config_path.
        """
        if config and config_path:
            raise ValueError("Provide either 'config_path' or 'config', not both.")

        self.config_path = config_path
        self.config = config or self._load_config()
        self.retrieval_components = self._load_pipeline_components("pipeline_retrieval")
        self.indexing_components = self._load_pipeline_components("pipeline_indexing")

    def _load_config(self) -> dict:
        """Load the YAML configuration file if config_path is provided."""
        if not self.config_path:
            raise ValueError("Either 'config_path' or 'config' must be provided.")
        with open(self.config_path, "r") as file:
            return yaml.safe_load(file)

    def _load_pipeline_components(self, pipeline_key: str) -> list[PipelineComponent]:
        """Load pipeline components based on the configuration."""
        components = []
        for component_config in self.config.get(pipeline_key, []):
            component_type = component_config["component"]  # e.g., chunker
            class_name = component_config["implementation"]  # e.g., FixedSizeChunker
            resources = component_config.get("resources", {})
            args = component_config.get("args", {})
            component_instance = self._component_factory(
                component_type, class_name, resources, args
            )
            components.append(component_instance)
        return components

    def _component_factory(
        self, component_type: str, class_name: str, resources: dict, args: dict
    ) -> PipelineComponent:
        """Dynamically import a class from a module and instantiate it with resources."""
        # Determine module and file paths
        module_name = f"src.components.{component_type}s"
        file_name = self._camel_to_snake(class_name)
        full_module_name = f"{module_name}.{file_name}"

        # Import the module and get the class
        module = importlib.import_module(full_module_name)
        component_class = getattr(module, class_name, None)
        if component_class is None:
            raise ValueError(f"Component {class_name} not found in module {full_module_name}.")

        # Resolve resources and args
        resolved_resources = {k: self._resolve_resource(k, v) for k, v in resources.items()}
        args = args or {}  # Default to empty dict if no args provided

        return component_class(**resolved_resources, **args)

    @staticmethod
    def _resolve_resource(resource_key: str, resource_value: str):
        """Resolve a resource by dynamically importing it from the appropriate module."""
        module_name = f"src.resources.{resource_key}s"
        module = importlib.import_module(module_name)
        return getattr(module, resource_value)

    @staticmethod
    def _camel_to_snake(camel_str: str) -> str:
        """Convert CamelCase to snake_case."""
        return "".join(["_" + c.lower() if c.isupper() else c for c in camel_str]).lstrip("_")

    def _run_pipeline(self, data: Data, components: list[PipelineComponent]) -> Data:
        """Run a series of components on the given data."""
        for component in components:
            try:
                data = component.process(data)
            except ValidationError as e:
                raise ValueError(f"Invalid data passed to {component.__class__.__name__}: {e}")
        return data

    def run_retrieval(self, data: Data) -> Data:
        """Run the retrieval pipeline."""
        return self._run_pipeline(data, self.retrieval_components)

    def run_indexing(self, data: Data) -> Data:
        """Run the indexing pipeline."""
        return self._run_pipeline(data, self.indexing_components)

    def run_combined(self, data: Data) -> Data:
        """Run the indexing pipeline first, followed by the retrieval pipeline."""
        data = self.run_indexing(data)
        data = self.run_retrieval(data)
        return data


if __name__ == "__main__":
    pipeline = Pipeline(config_path="config.yaml")

    # Example for combined pipeline
    query = Query(text="What is the best peanut butter? Answer in max 3 words.")
    actual_answer = "Calvé Pindakaas"
    data = Data(queries=[query], actual_answer=actual_answer)
    combined_result = pipeline.run_combined(data)
    print("Combined Result:", combined_result)
