import textwrap

import pytest

from polar.lang import RuleNode
from polar.lang.all import SimpleResponse
from polar.lang.eval import Bot
from polar.lang.json_import import load, load_bot_rule, load_bot_rule_content

FAKE_TEMPLATE_ID = "c3487788-ff34-4188-a781-21527911e4c5"


def test_rule_abc_cde():
    js = {
        "flow": [
            {
                "args": [
                    {
                        "args": [
                            {
                                "node": "term",
                                "type": "string",
                                "value": "abc"
                            }
                        ],
                        "node": "regexp_rule"
                    }
                ],
                "node": "rule"
            },
            {
                "args": [
                    {
                        "node": "term",
                        "type": "string",
                        "value": "def"
                    }
                ],
                "node": "response"
            }
        ],
        "node": "flow"
    }
    flow = load(js)

    assert len(flow.commands) == 2
    assert isinstance(flow.commands[0], RuleNode)
    assert isinstance(flow.commands[1], SimpleResponse)

    bot = Bot()
    load_bot_rule(bot, js)

    p = 0
    assert len(bot.rules) == 1


def test():
    bot = Bot()
    data = """
$ abc
# def
""".strip()
    load_bot_rule_content(bot, data)

    p = 0


if __name__ == "__main__":
    pytest.main(["-s", "-x", __file__])

