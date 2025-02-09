from typing import Any

from pydantic import BaseModel


class Field(BaseModel):
    label: str = ""
    type: str = ""
    param_name: str = ""
    param_type: Any = None


class ComponentConfig(BaseModel):
    name: str = ""
    available_implementations: list[str] = []
    implementation: str = ""
    constructor_params: dict = {}
    resources: dict = {}
    args: dict = {}
    phase: str = ""
    fields: list[Field] = []

    def to_dict(self) -> dict:
        """Convert a ComponentConfig object into a dictionary matching the YAML structure."""
        config_dict = {
            "component": self.name,
            "implementation": self.implementation,
        }

        # Only include resources and args if they exist (to match YAML structure)
        if self.resources:
            config_dict["resources"] = self.resources
        if self.args:
            config_dict["args"] = self.args

        return config_dict
