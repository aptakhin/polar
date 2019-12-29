import asyncio

import pytest

from polar.lang import UserMessage, Context, MatchRange, Interactivity
from polar.lang.regex_rule import RegexRule


def test_word():
    format_word = lambda test: RegexRule.Node._format_word(test)
    assert format_word("abyr") == r"abyr"
    assert format_word("зайч~") == r"зайч\w."


def test_build():
    build = lambda test: RegexRule(test).build_re()
    assert build(["abyr"]) == r"(abyr)"
    assert build(["зайч~"]) == r"(зайч\w.)"

    assert build([["1", "2", "3"]]) == r"(1|2|3)"
    assert build([["1", "2", "3"], ["4", "5", "6"]]) == r"(1|2|3)\s+?(4|5|6)"
    assert build([["1", "2", "3"], RegexRule.Any, "abyr"]) == r"(1|2|3)(.*)(abyr)"

    assert build([["зайч~", "мальчик"]]) == r"(зайч\w.|мальчик)"

    assert build(["cat", RegexRule.Any]) == r"(cat)(.*)"
    assert build(["cat", RegexRule.Any, "dog"]) == r"(cat)(.*)(dog)"
    assert build([RegexRule.Any, "dog"]) == r"(.*)(dog)"


def test_rabbit():
    args = [
        ["1", "2", "3"],
        "вышел",
        ["зайч~", "маль~"],
    ]

    rv = RegexRule(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("1 вышел зайчик"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14, 3)

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("2 вышел мальчик"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14, 3)


def test_star():
    args = [
        RegexRule.Any,
    ]

    rv = RegexRule(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("cat"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 3, rv.ANY_WEIGHT)


def test_star_merge():
    args = [
        "cat",
        RegexRule.Any,
    ]

    rv = RegexRule(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("cat"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 3, 1 - rv.ANY_WEIGHT)


def test_weighted_rabbit():
    args = [
        RegexRule.Node(["1", "2", "3"]),
        RegexRule.Node("вышел", weight=2),
        RegexRule.Node(["зайч~", "маль~"]),
    ]

    rv = RegexRule(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("1 вышел зайчик"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14, 4)


if __name__ == "__main__":
    pytest.main(["-s", "-x", __file__])
