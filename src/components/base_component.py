from abc import ABC, abstractmethod

from src.models import Data


class PipelineComponent(ABC):
    def process(self, data: Data) -> Data:
        self.validate_input_data(data)
        inputs = self.extract_input(data)
        if isinstance(inputs, tuple):  # Avoid unpacking if `inputs` is not a tuple
            result = self.run(*inputs)
        elif inputs is None:
            result = self.run()
        else:
            result = self.run(inputs)
        self.update_data(data, result)
        return data

    @abstractmethod
    def validate_input_data(self, data: Data):
        pass

    @abstractmethod
    def extract_input(self, data: Data):
        """Extract input arguments from the Data object."""
        pass

    @abstractmethod
    def run(self, *args):
        pass

    @abstractmethod
    def update_data(self, data: Data, result):
        """Define how the result is loaded back into the `Data` object."""
        pass
