from domain.output_contract import validate_llm_output


def test_parse_valid_review_contract_json():
    content = """
    {
      "pr_comments": [
        {
          "file": "application/webhook_fetch.py",
          "line": 42,
          "severity": "medium",
          "category": "validation",
          "message": "Write-back should only occur after contract validation.",
          "rationale": "Invalid LLM output must not propagate to GitHub or Jira."
        }
      ],
      "qa_checklist": [
        {
          "title": "Validate contract enforcement",
          "steps": [
            "Send malformed LLM output",
            "Confirm write-back is blocked"
          ],
          "acceptance_criteria_ref": "OPRC-3",
          "expected_result": "No GitHub or Jira write-back occurs"
        }
      ]
    }
    """

    result = validate_llm_output(content)

    assert result.valid is True
    assert result.output is not None
    assert len(result.output.pr_comments) == 1
    assert len(result.output.qa_checklist) == 1
