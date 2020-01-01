import pytest

from polar.lang import OutMessageEvent, UserMessage
from polar.lang.all import SimpleResponse, Flow
from polar.lang.eval import Bot, Rule
from polar.lang.regex_rule import RegexRule
from tests.logic import execute_event


def test_trivial_logic():
    bot = Bot()

    rule_mind = Rule(name="name")
    rule_mind.condition = Flow([
        RegexRule([
            ["1", "2", "3"],
            "вышел",
            ["зайч~", "маль~"],
        ])
    ])
    rule_mind.flow = Flow([
        SimpleResponse([OutMessageEvent("И, правда, вышел")]),
    ])

    rule_mind2 = Rule(name="name")
    rule_mind2.condition = Flow([
        RegexRule([
            "крокодил",
        ])
    ])
    rule_mind2.flow = Flow([
        SimpleResponse([OutMessageEvent("слон")]),
    ])

    bot.add_rules([rule_mind, rule_mind2])

    event = UserMessage("2 вышел зайчик")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "И, правда, вышел"
    assert state.sorted_results[0][1].ranges[0].weight == 3

    event = UserMessage("крокодил")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "слон"
    assert state.sorted_results[0][1].ranges[0].weight == 1


def test_star_logic():
    bot = Bot()

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                RegexRule.Any,
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("any")]),
        ])
    ))

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                "cat",
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("dog")]),
        ])
    ))

    event = UserMessage("dog")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "any"
    assert state.sorted_results[0][1].ranges[0].weight == RegexRule.ANY_WEIGHT

    event = UserMessage("cat")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "dog"
    assert state.sorted_results[0][1].ranges[0].weight == 1


def test_star_logic2():
    bot = Bot()

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                RegexRule.Any,
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("any")]),
        ])
    ))

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                "cat"
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("dog1")]),
        ])
    ))

    bot.add_rule(Rule(
        condition=Flow([
            RegexRule([
                RegexRule.Any, "cat", RegexRule.Any
            ])
        ]),
        flow=Flow([
            SimpleResponse([OutMessageEvent("dog2")]),
        ])
    ))

    event = UserMessage("cat")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "dog1"

    assert state.sorted_results[0][1].ranges[0].weight == 1 and state.sorted_results[0][0] == 1
    assert state.sorted_results[1][1].ranges[0].weight == 1 - 2 * RegexRule.ANY_WEIGHT and state.sorted_results[1][0] == 2
    assert state.sorted_results[2][1].ranges[0].weight == RegexRule.ANY_WEIGHT and state.sorted_results[2][0] == 0

    event = UserMessage("cat other")
    resp_events, state = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "dog2"

    assert state.sorted_results[0][1].ranges[0].weight == 1 and state.sorted_results[0][0] == 2
    assert state.sorted_results[1][1].ranges[0].weight == 1 and state.sorted_results[1][0] == 1
    assert state.sorted_results[2][1].ranges[0].weight == RegexRule.ANY_WEIGHT and state.sorted_results[2][0] == 0


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
