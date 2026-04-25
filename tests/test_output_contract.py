from domain.output_contract import validate_llm_output


def test_valid_output_passes():
    raw = """
    {
      "pr_comments": [
        {
          "file": "application/webhook_fetch.py",
          "line": 42,
          "severity": "medium",
          "category": "validation",
          "message": "Missing validation before write-back.",
          "rationale": "Invalid LLM output could reach GitHub or Jira."
        }
      ],
      "qa_checklist": [
        {
          "title": "Validate rejected LLM output",
          "steps": [
            "Trigger webhook with malformed LLM output",
            "Confirm no GitHub comment is written",
            "Confirm no Jira checklist is written"
          ],
          "acceptance_criteria_ref": "Output contract enforcement",
          "expected_result": "Write-back is blocked"
        }
      ]
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is True
    assert result.output is not None
    assert result.errors == []


def test_missing_pr_comments_fails():
    raw = """
    {
      "qa_checklist": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "Missing top-level key: pr_comments" in result.errors


def test_missing_qa_checklist_fails():
    raw = """
    {
      "pr_comments": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "Missing top-level key: qa_checklist" in result.errors


def test_plain_markdown_fails():
    raw = """
    ## Review

    Looks fine.
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "LLM output is not a valid JSON object" in result.errors


def test_empty_json_fails():
    raw = "{}"

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "Missing top-level key: pr_comments" in result.errors
    assert "Missing top-level key: qa_checklist" in result.errors


def test_empty_contract_fails():
    raw = """
    {
      "pr_comments": [],
      "qa_checklist": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert (
        "LLM output must contain at least one PR comment or QA checklist item"
        in result.errors
    )


def test_invalid_comment_shape_fails():
    raw = """
    {
      "pr_comments": [
        {
          "file": "x.py",
          "line": 1,
          "comment": "Old shape"
        }
      ],
      "qa_checklist": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert any("pr_comments[0] missing keys" in error for error in result.errors)
    assert any("pr_comments[0] unknown keys" in error for error in result.errors)


def test_invalid_checklist_shape_fails():
    raw = """
    {
      "pr_comments": [],
      "qa_checklist": [
        {
          "item": "Old checklist shape",
          "status": "pending"
        }
      ]
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert any("qa_checklist[0] missing keys" in error for error in result.errors)
    assert any("qa_checklist[0] unknown keys" in error for error in result.errors)


def test_invalid_severity_fails():
    raw = """
    {
      "pr_comments": [
        {
          "file": "x.py",
          "line": 1,
          "severity": "critical",
          "category": "validation",
          "message": "Message",
          "rationale": "Rationale"
        }
      ],
      "qa_checklist": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "pr_comments[0].severity is invalid" in result.errors


def test_invalid_category_fails():
    raw = """
    {
      "pr_comments": [
        {
          "file": "x.py",
          "line": 1,
          "severity": "high",
          "category": "performance",
          "message": "Message",
          "rationale": "Rationale"
        }
      ],
      "qa_checklist": []
    }
    """

    result = validate_llm_output(raw)

    assert result.valid is False
    assert "pr_comments[0].category is invalid" in result.errors
