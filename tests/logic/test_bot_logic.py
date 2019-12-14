import asyncio

from polar import Bot, Rule, RegexVariative, Flow, SimpleResponse, OutMessageEvent, Context, Executor, \
    UserMessage


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

    context = Context()
    context["random_seed"] = 123
    executor = Executor()

    event = UserMessage("2 вышел зайчик")
    resp_event = asyncio.get_event_loop().run_until_complete(executor.execute_event(event=event, bot=bot, context=context))
    assert len(resp_event) == 1
    assert len(resp_event[0].parts) == 1
    assert resp_event[0].parts[0] == "И, правда, вышел"

    event = UserMessage("крокодил")
    resp_event = asyncio.get_event_loop().run_until_complete(
        executor.execute_event(event=event, bot=bot, context=context))
    assert len(resp_event) == 1
    assert len(resp_event[0].parts) == 1
    assert resp_event[0].parts[0] == "слон"


test_logic()
