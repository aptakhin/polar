from polar import RegexVariative, SimpleResponse, OutMessageEvent
from polar.logic.parser import ArmBotParser


FAKE_TEMPLATE_ID = "c3487788-ff34-4188-a781-21527911e4c5"

def test_rule_parse_any():
    template = {
        "content": "<div>$ *</div><div># 1</div>",
        "template_id": FAKE_TEMPLATE_ID,
    }

    rule = ArmBotParser.parse_rule(template)

    assert rule.name == template["template_id"]
    assert rule.condition.commands[0].args == [RegexVariative.Any]
    assert len(rule.flow.commands) == 1
    assert isinstance(rule.flow.commands[0], SimpleResponse)
    assert rule.flow.commands[0].responses[0].parts == ["1"]


def test_rule_parse_cat():
    template = {
        "content": "<div>$ cat *</div><div># 1</div>",
        "template_id": FAKE_TEMPLATE_ID,
    }

    rule = ArmBotParser.parse_rule(template)

    assert rule.name == template["template_id"]
    assert rule.condition.commands[0].args == ["cat", RegexVariative.Any]
    assert len(rule.flow.commands) == 1
    assert isinstance(rule.flow.commands[0], SimpleResponse)
    assert rule.flow.commands[0].responses[0].parts == ["1"]


#
# def test_parser():
#
#     templates = [
#         {
#             "content": "<div>$ *</div><div># 1</div>",
#         }
#     ]
#
#     parser = ArmBotParser()
#     bot = parser.load_bot(templates)


test_rule_parse_cat()
