from dataclasses import dataclass, field
from typing import Any, Literal


Severity = Literal["low", "medium", "high"]

ReviewCategory = Literal[
    "correctness",
    "validation",
    "security",
    "data_handling",
    "acceptance_criteria",
    "regression",
    "maintainability",
]


@dataclass(frozen=True)
class PullRequest:
    pr_id: int
    branch: str
    title: str


@dataclass(frozen=True)
class Ticket:
    key: str
    summary: str
    description: str


@dataclass(frozen=True)
class PRComment:
    file: str
    line: int
    severity: Severity
    category: ReviewCategory
    message: str
    rationale: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PRComment":
        return PRComment(
            file=str(data["file"]).strip(),
            line=int(data["line"]),
            severity=data["severity"],
            category=data["category"],
            message=str(data["message"]).strip(),
            rationale=str(data["rationale"]).strip(),
        )


@dataclass(frozen=True)
class QAChecklistItem:
    title: str
    steps: list[str]
    acceptance_criteria_ref: str
    expected_result: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "QAChecklistItem":
        return QAChecklistItem(
            title=str(data["title"]).strip(),
            steps=[str(step).strip() for step in data["steps"]],
            acceptance_criteria_ref=str(data["acceptance_criteria_ref"]).strip(),
            expected_result=str(data["expected_result"]).strip(),
        )


@dataclass(frozen=True)
class LLMReviewOutput:
    pr_comments: list[PRComment] = field(default_factory=list)
    qa_checklist: list[QAChecklistItem] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LLMReviewOutput":
        return LLMReviewOutput(
            pr_comments=[
                PRComment.from_dict(item)
                for item in data["pr_comments"]
            ],
            qa_checklist=[
                QAChecklistItem.from_dict(item)
                for item in data["qa_checklist"]
            ],
        )


@dataclass(frozen=True)
class OutputValidationResult:
    valid: bool
    output: LLMReviewOutput | None = None
    errors: list[str] = field(default_factory=list)
