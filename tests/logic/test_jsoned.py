import pytest

from polar.lang import OutMessageEvent, UserMessage
from polar.lang.all import SimpleResponse, Flow
from polar.lang.eval import Bot, Rule
from polar.lang.regex_rule import RegexRule
from tests.logic import execute_event


def test_cat_dog():
    bot = Bot()

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                RegexRule.Any,
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("*")]),
        ])
    ))

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                "cat", "dog"
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("cat dog")]),
        ])
    ))

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                "cat", RegexRule.Any
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("cat *")]),
        ])
    ))

    event = UserMessage("cat dog")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "cat dog"

    assert state.sorted_results[0][1].ranges[0].weight == 2
    assert state.sorted_results[1][1].ranges[0].weight == 1 + RegexRule.ANY_WEIGHT
    assert state.sorted_results[2][1].ranges[0].weight == RegexRule.ANY_WEIGHT


if __name__ == "__main__":
    pytest.main(["-s", "-x", __file__])
