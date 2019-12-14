import asyncio

from polar import RegexVariative, UserMessage, Context, MatchRange


def test_word():
    format = RegexVariative._format_word
    assert format("abyr") == r"abyr"
    assert format("зайч~") == r"зайч\w."


def test_build():
    build = RegexVariative._build_re
    assert build(["abyr"]) == r"abyr"
    assert build(["зайч~"]) == r"зайч\w."

    assert build([["1", "2", "3"]]) == r"(1|2|3)"
    assert build([["1", "2", "3"], RegexVariative.Any, "abyr"]) == r"(1|2|3) .* abyr"

    assert build([["зайч~", "мальчик"]]) == r"(зайч\w.|мальчик)"


def test_rabbit():
    args = [
        ["1", "2", "3"],
        "вышел",
        ["зайч~", "маль~"],
    ]

    rv = RegexVariative(args)

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("1 вышел зайчик"), Context()))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14)

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("2 вышел мальчик"), Context()))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14)
