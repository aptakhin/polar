import textwrap

import pytest

from polar import RegexVariative, SimpleResponse
from polar.logic.parser import ArmBotParser


FAKE_TEMPLATE_ID = "c3487788-ff34-4188-a781-21527911e4c5"

def _content(content):
    dedented = textwrap.dedent(content).strip()
    html = "<div>" + "</div><div>".join(dedented.split("\n")) + "</div>"
    return html


def test_rule_parse_any():
    template = {
        "content": _content("""
            $ *
            # 1
        """),
        "id": FAKE_TEMPLATE_ID,
    }

    rule = ArmBotParser.parse_rule(template)

    assert rule.name == template["id"]
    # assert rule.condition.commands[0].args == [RegexVariative.Node(RegexVariative.Any)]
    assert len(rule.flow.commands) == 1
    assert isinstance(rule.flow.commands[0], SimpleResponse)
    assert rule.flow.commands[0].responses[0].parts == ["1"]


def test_rule_parse_cat():
    template = {
        "content": _content("""
            $ cat *
            # 1
        """),
        "id": FAKE_TEMPLATE_ID,
    }

    rule = ArmBotParser.parse_rule(template)

    assert rule.name == template["id"]
    # assert rule.condition.commands[0].args == [RegexVariative.Node("cat"), RegexVariative.Node(RegexVariative.Any)]
    assert len(rule.flow.commands) == 1
    assert isinstance(rule.flow.commands[0], SimpleResponse)
    assert rule.flow.commands[0].responses[0].parts == ["1"]


if __name__ == "__main__":
    pytest.main(["-s", "-x", __file__])

