import asyncio

from polar import RegexVariative, UserMessage, Context


def test_build():
    RegexVariative._b

def test_a():
    args = [
        ["1", "2", "3"],
        "вышел",
        ["зайч~", "маль~"],
    ]

    rv = RegexVariative(args)

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("1 вышел зайчик"), Context()))

    print(resp)


test_build()
test_a()
