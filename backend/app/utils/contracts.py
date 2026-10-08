"""Contract validation utilities linking backend schemas to shared JSON schemas.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Enforces contract adherence across module boundaries using Draft 2020-12 specifications.
"""

import json
from pathlib import Path
from typing import Any, Dict
from jsonschema import Draft202012Validator
from pydantic import BaseModel


def get_contracts_directory() -> Path:
    """Return the absolute path to the root /contracts directory."""
    return Path(__file__).resolve().parent.parent.parent.parent / "contracts"


def load_json_schema(schema_filename: str) -> Dict[str, Any]:
    """Load and parse a JSON schema file from /contracts.

    Args:
        schema_filename: Filename (e.g., 'vision_result.schema.json')

    Returns:
        dict: Parsed JSON schema dictionary.
    """
    schema_path = get_contracts_directory() / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Contract schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_contract(instance_data: Dict[str, Any], schema_filename: str) -> None:
    """Validate a dictionary instance against a contract schema.

    Args:
        instance_data: Data payload to validate
        schema_filename: Name of the schema file in /contracts

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    schema = load_json_schema(schema_filename)
    Draft202012Validator(schema).validate(instance_data)


def validate_model_against_contract(model_instance: BaseModel, schema_filename: str) -> None:
    """Validate a Pydantic model instance against a contract schema.

    Args:
        model_instance: Pydantic model instance
        schema_filename: Name of the schema file in /contracts

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    payload = model_instance.model_dump(mode="json", exclude_none=True)
    validate_against_contract(payload, schema_filename)
