from polar import Bot, Rule, RegexVariative, Flow, SimpleResponse, OutMessageEvent, \
    UserMessage
from tests.logic import execute_event


def test_logic():
    bot = Bot()

    rule_mind = Rule(name="name")
    rule_mind.condition = Flow([
        RegexVariative([
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
        RegexVariative([
            "крокодил",
        ])
    ])
    rule_mind2.flow = Flow([
        SimpleResponse([OutMessageEvent("слон")]),
    ])

    bot.add_rules([rule_mind, rule_mind2])

    event = UserMessage("2 вышел зайчик")
    resp_events = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "И, правда, вышел"

    event = UserMessage("крокодил")
    resp_events = execute_event(event=event, bot=bot)
    assert len(resp_events) == 1
    assert len(resp_events[0].parts) == 1
    assert resp_events[0].parts[0] == "слон"


test_logic()
