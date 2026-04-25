import json
import re
from typing import Any

from domain.models import LLMReviewOutput, OutputValidationResult

ALLOWED_TOP_LEVEL_KEYS = {
    "pr_comments",
    "qa_checklist",
}

ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
}

ALLOWED_CATEGORIES = {
    "risk",
    "validation",
    "consistency",
}

MAX_PR_MESSAGE_LENGTH = 240
MAX_PR_RATIONALE_LENGTH = 500
MAX_QA_TITLE_LENGTH = 160
MAX_QA_STEP_LENGTH = 240
MAX_QA_ACCEPTANCE_REF_LENGTH = 160
MAX_QA_EXPECTED_RESULT_LENGTH = 240


def validate_llm_output(raw_content: str | None) -> OutputValidationResult:
    parsed = _parse_json_object(raw_content)

    if parsed is None:
        return OutputValidationResult(
            valid=False,
            errors=["LLM output is not a valid JSON object"],
        )

    errors = _validate_shape(parsed)

    if errors:
        return OutputValidationResult(
            valid=False,
            errors=errors,
        )

    try:
        output = LLMReviewOutput.from_dict(parsed)
    except (KeyError, TypeError, ValueError) as exc:
        return OutputValidationResult(
            valid=False,
            errors=[f"LLM output could not be converted: {exc}"],
        )

    return OutputValidationResult(
        valid=True,
        output=output,
        errors=[],
    )


def _parse_json_object(raw_content: str | None) -> dict[str, Any] | None:
    if not raw_content:
        return None

    content = raw_content.strip()

    fenced_match = re.fullmatch(
        r"```json\s*(\{.*\})\s*```",
        content,
        re.DOTALL,
    )

    if fenced_match:
        content = fenced_match.group(1).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed


def _validate_shape(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    unknown_keys = set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        errors.append(f"Unknown top-level keys: {sorted(unknown_keys)}")

    for required_key in ALLOWED_TOP_LEVEL_KEYS:
        if required_key not in data:
            errors.append(f"Missing top-level key: {required_key}")

    if errors:
        return errors

    if not isinstance(data["pr_comments"], list):
        errors.append("pr_comments must be a list")

    if not isinstance(data["qa_checklist"], list):
        errors.append("qa_checklist must be a list")

    if errors:
        return errors

    for index, comment in enumerate(data["pr_comments"]):
        errors.extend(_validate_pr_comment(comment, index))

    for index, item in enumerate(data["qa_checklist"]):
        errors.extend(_validate_qa_checklist_item(item, index))

    return errors


def _validate_pr_comment(comment: Any, index: int) -> list[str]:
    errors: list[str] = []

    if not isinstance(comment, dict):
        return [f"pr_comments[{index}] must be an object"]

    required = {
        "file",
        "line",
        "severity",
        "category",
        "message",
        "rationale",
    }

    missing = required - set(comment.keys())
    unknown = set(comment.keys()) - required

    if missing:
        errors.append(f"pr_comments[{index}] missing keys: {sorted(missing)}")

    if unknown:
        errors.append(f"pr_comments[{index}] unknown keys: {sorted(unknown)}")

    if errors:
        return errors

    if not _non_empty_string(comment["file"]):
        errors.append(f"pr_comments[{index}].file must be non-empty text")

    if not isinstance(comment["line"], int) or comment["line"] < 1:
        errors.append(f"pr_comments[{index}].line must be a positive integer")

    if comment["severity"] not in ALLOWED_SEVERITIES:
        errors.append(f"pr_comments[{index}].severity is invalid")

    if comment["category"] not in ALLOWED_CATEGORIES:
        errors.append(f"pr_comments[{index}].category is invalid")

    if not _non_empty_string(comment["message"]):
        errors.append(f"pr_comments[{index}].message must be non-empty text")

    if not _non_empty_string(comment["rationale"]):
        errors.append(f"pr_comments[{index}].rationale must be non-empty text")

    if _non_empty_string(comment["message"]) and not _within_length(
            comment["message"],
            MAX_PR_MESSAGE_LENGTH,
    ):
        errors.append(
            f"pr_comments[{index}].message exceeds {MAX_PR_MESSAGE_LENGTH} characters"
        )

    if _non_empty_string(comment["rationale"]) and not _within_length(
            comment["rationale"],
            MAX_PR_RATIONALE_LENGTH,
    ):
        errors.append(
            f"pr_comments[{index}].rationale exceeds {MAX_PR_RATIONALE_LENGTH} characters"
        )

    return errors


def _validate_qa_checklist_item(item: Any, index: int) -> list[str]:
    errors: list[str] = []

    if not isinstance(item, dict):
        return [f"qa_checklist[{index}] must be an object"]

    required = {
        "title",
        "steps",
        "acceptance_criteria_ref",
        "expected_result",
    }

    missing = required - set(item.keys())
    unknown = set(item.keys()) - required

    if missing:
        errors.append(f"qa_checklist[{index}] missing keys: {sorted(missing)}")

    if unknown:
        errors.append(f"qa_checklist[{index}] unknown keys: {sorted(unknown)}")

    if errors:
        return errors

    if not _non_empty_string(item["title"]):
        errors.append(f"qa_checklist[{index}].title must be non-empty text")

    if not isinstance(item["steps"], list) or not item["steps"]:
        errors.append(f"qa_checklist[{index}].steps must be a non-empty list")
    else:
        for step_index, step in enumerate(item["steps"]):
            if not _non_empty_string(step):
                errors.append(
                    f"qa_checklist[{index}].steps[{step_index}] must be non-empty text"
                )
            elif not _within_length(step, MAX_QA_STEP_LENGTH):
                errors.append(
                    f"qa_checklist[{index}].steps[{step_index}] exceeds {MAX_QA_STEP_LENGTH} characters"
                )

    if not _non_empty_string(item["acceptance_criteria_ref"]):
        errors.append(
            f"qa_checklist[{index}].acceptance_criteria_ref must be non-empty text"
        )

    if not _non_empty_string(item["expected_result"]):
        errors.append(
            f"qa_checklist[{index}].expected_result must be non-empty text"
        )

    if _non_empty_string(item["title"]) and not _within_length(
            item["title"],
            MAX_QA_TITLE_LENGTH,
    ):
        errors.append(
            f"qa_checklist[{index}].title exceeds {MAX_QA_TITLE_LENGTH} characters"
        )

    if _non_empty_string(item["acceptance_criteria_ref"]) and not _within_length(
            item["acceptance_criteria_ref"],
            MAX_QA_ACCEPTANCE_REF_LENGTH,
    ):
        errors.append(
            f"qa_checklist[{index}].acceptance_criteria_ref exceeds {MAX_QA_ACCEPTANCE_REF_LENGTH} characters"
        )

    if _non_empty_string(item["expected_result"]) and not _within_length(
            item["expected_result"],
            MAX_QA_EXPECTED_RESULT_LENGTH,
    ):
        errors.append(
            f"qa_checklist[{index}].expected_result exceeds {MAX_QA_EXPECTED_RESULT_LENGTH} characters"
        )

    return errors


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _within_length(value: Any, max_length: int) -> bool:
    return isinstance(value, str) and len(value.strip()) <= max_length
