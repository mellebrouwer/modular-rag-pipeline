from abc import ABC, abstractmethod

from src.models import Data


class PipelineComponent(ABC):
    """
    Abstract base class for pipeline components.

    Methods:
        process(data: Data) -> Data:
            Process the data through the component.
        validate_input_data(data: Data):
            Validate the input data.
        extract_input(data: Data):
            Extract input arguments from the Data object.
        run(*args):
            Run the component's main logic.
        update_data(data: Data, result):
            Update the data object with the result.
    """

    def process(self, data: Data) -> Data:
        """
        Process the data through the component.

        Args:
            data (Data): The data to be processed.

        Returns:
            Data: The processed data.
        """
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
        """
        Validate the input data.

        Args:
            data (Data): The data to be validated.
        """
        pass

    @abstractmethod
    def extract_input(self, data: Data):
        """
        Extract input arguments from the Data object.

        Args:
            data (Data): The data object to extract input from.

        Returns:
            The extracted input arguments.
        """
        pass

    @abstractmethod
    def run(self, *args):
        """
        Run the component's main logic.

        Args:
            *args: The input arguments for the component.

        Returns:
            The result of the component's logic.
        """
        pass

    @abstractmethod
    def update_data(self, data: Data, result):
        """
        Update the data object with the result.

        Args:
            data (Data): The data object to be updated.
            result: The result to update the data with.
        """
        pass
