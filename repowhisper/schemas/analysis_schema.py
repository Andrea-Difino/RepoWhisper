from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ModuleAnalysisItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    code_snippet: str
    notes: dict[str, str] = Field(default_factory=dict)

    @field_validator("notes")
    @classmethod
    def validate_line_numbers(cls, value: dict[str, str]) -> dict[str, str]:
        for line_key, note_text in value.items():
            if not line_key.isdigit() or int(line_key) <= 0:
                raise ValueError(f"Raw number not valid in 'notes': '{line_key}'")
            if not note_text.strip():
                raise ValueError(f"Note for row {line_key} can't be empty")
        return value

class RepoWhisperReport(BaseModel):
    title: str = Field(min_length=1)
    tree_structure: str = Field(min_length=1)
    narrative: str = Field(min_length=1)
    raw_modules: list[ModuleAnalysisItem] = Field(min_length=1)

class AnalysisJsonValidator:
    """Deterministic validator for the JSON output generated or loaded in RepoWhisper."""

    @staticmethod
    def validate_string(raw_json: str) -> RepoWhisperReport:
        """
        Validate a raw JSON string.
        Raise ValueError it the structure don't correspond to the schema.

        Args:
            raw_json (str): string of the json to be validated
        """
        try:
            return RepoWhisperReport.model_validate_json(raw_json)
        except ValidationError as e:
            raise ValueError(f"JSON report structure not valid: \n{e}") from e

    @staticmethod
    def validate_file(file_path: str | Path) -> RepoWhisperReport:
        """
        Read and validate a JSON file before being passed to React interface.

        Args:
            file_path (str | Path) : path of the JSON file to be validated
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"JSON file not found: {path}")

        raw_content = path.read_text(encoding="utf-8")
        return AnalysisJsonValidator.validate_string(raw_content)