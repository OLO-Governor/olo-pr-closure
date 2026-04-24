from domain.services import parse_llm_output


def test_parse_valid_json():
    content = '{"comments": [], "checklist": []}'
    result = parse_llm_output(content)
    assert "comments" in result
    assert "checklist" in result
