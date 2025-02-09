import os
import re

import yaml


def load_config() -> dict:
    """
    Load the YAML configuration file.

    Returns:
        dict: The loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file is not found.
    """
    config_file = os.path.join(os.getcwd(), "config.yaml")
    if not os.path.exists(config_file):
        raise FileNotFoundError("No config.yaml file found in the current working directory.")

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_qa_file(qa_file_path: str) -> list[dict]:
    """
    Load Q&A pairs from a YAML file.

    Args:
        qa_file_path (str): Path to the Q&A YAML file.

    Returns:
        list[dict]: A list of Q&A pairs.
    """
    if not os.path.exists(qa_file_path):
        return []
    with open(qa_file_path, "r") as f:
        return yaml.safe_load(f)

def find_class_name_in_file(file_path: str) -> str:
    """
    Extract the class name from a Python file.

    Args:
        file_path (str): Path to the Python file.

    Returns:
        str: The class name, or an empty string if no class is found.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r"class\s+([A-Z]\w+)", content)
        if match:
            return match.group(1)
    return ""

def camel_to_snake(name: str) -> str:
    """
    Convert a CamelCase string to snake_case.

    Args:
        name (str): The CamelCase string.

    Returns:
        str: The snake_case equivalent.
    """
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")

def prettify_title(text: str) -> str:
    """
    Convert a string with underscores into a prettified title.
    Capitalizes each word and replaces underscores with spaces.

    Args:
        text (str): The input string to prettify.

    Returns:
        str: Prettified string.
    """
    return " ".join(word.capitalize() for word in text.split("_"))