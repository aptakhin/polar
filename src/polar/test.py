import asyncio

from polar import Executor, Anchor, AnchorFeature, Bot, Rule, Flow, Regexp, SimpleResponse, OutMessageEvent, \
    ExitAstNode, \
    Set, NotEmpty, If, NameFeature, ConsoleIO, Context, UserMessage, Empty, Print


async def test_anchor():
    anchors = [
        Anchor("в", +1),
        Anchor("во", +1),
    ]
    feat = AnchorFeature(anchors=anchors, var=None)
    context = Context()
    resp = await feat.eval(UserMessage("во Владивосток"), context=context)
    res = resp.value.value
    assert len(res) == 1
    assert res[0]["idx"] == 0
    assert res[0]["match"] == ["Владивосток"]

    anchors = [
        Anchor("меня", 1),
        Anchor("меня", -1),
        Anchor("зовут", -1),
        Anchor("зовут", +1),
    ]
    feat = AnchorFeature(anchors=anchors, var=None)
    context = Context()
    res = await feat.eval(UserMessage("Сашей меня зовут все"), context=context)
    # assert context[var] == ["Сашей"]
    p = 0


def test():
    asyncio.get_event_loop().run_until_complete(test_anchor())

    bot = Bot()

    rule_hi_stop = Rule(name="name")
    rule_hi_stop.condition = Flow([
        Regexp(["привет_как_дела"]),
    ])
    rule_hi_stop.flow = Flow([
        SimpleResponse([OutMessageEvent("И_тебе_привет")]),
        Set("secret", "1"),
        ExitAstNode(),
    ])

    rule_hi = Rule(name="name")
    rule_hi.condition = Flow([
        Regexp(["привет", "прив"]),
    ])
    rule_hi.flow = Flow([
        If(Empty("name"),
            then_=Flow([
                If(Empty("greeted"),
                   then_=Flow([
                       SimpleResponse([OutMessageEvent("И тебе привет"), OutMessageEvent("Приветище!")]),
                   ]),
                   else_=Flow([
                       SimpleResponse(["И снова привет!", "Приветище ещё раз!"]),
                   ]),
                )
            ]),
            else_=Flow([
                If(Empty("greeted"),
                   then_=Flow([
                       SimpleResponse([OutMessageEvent(["Привет, ", Print("name"), "!"])]),
                   ]),
                   else_=Flow([
                       SimpleResponse([OutMessageEvent([Print("name"), ", привет ещё раз!"])]),
                   ]),
                )
            ]),
        ),
        Set("greeted", "1"),
    ])

    rule_mind = Rule(name="name")
    rule_mind.condition = Flow([
        Regexp(["как дела", "дела"]),
    ])
    rule_mind.flow = Flow([
        SimpleResponse([OutMessageEvent("Дела супер!"), OutMessageEvent("Дела отлично!")]),
        SimpleResponse([OutMessageEvent("Да-да")]),
        SimpleResponse([OutMessageEvent("Как у тебя?"), OutMessageEvent("")]),
    ])

    vocab = {
        "сашей": {"norm": "Саша"},
        "саша": {"norm": "Саша"},
        "машей": {"norm": "Маша"},
        "маша": {"norm": "Маша"},
    }

    rule_name = Rule(name="name")
    rule_name.condition = Flow([
        NameFeature(vocab=vocab, var="name"),
    ])
    rule_name.flow = Flow([
    ])

    bot.add_rules([rule_name, rule_hi_stop, rule_hi, rule_mind])

    console_io = ConsoleIO()
    context = Context()
    context["random_seed"] = 123
    executor = Executor()

    asyncio.get_event_loop().run_until_complete(executor.loop(bot=bot, context=context, io=console_io))

    # from src.polar import json_serializer
    # out = json_serializer.dump(bot)
    # import json
    # # print(json.dumps(out, indent=2, ensure_ascii=False))
    # read_bot = json_serializer.load(out)
    # with open("test.json", "w") as f:
    #     json.dump(out, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    test()
