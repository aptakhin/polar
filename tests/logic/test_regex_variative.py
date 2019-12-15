import asyncio

import pytest

from polar import RegexVariative, UserMessage, Context, MatchRange, Interactivity


def test_word():
    format = RegexVariative._format_word
    assert format("abyr") == r"abyr"
    assert format("зайч~") == r"зайч\w."


def test_build():
    build = RegexVariative._build_re
    assert build(["abyr"]) == r"(abyr)"
    assert build(["зайч~"]) == r"(зайч\w.)"

    assert build([["1", "2", "3"]]) == r"(1|2|3)"
    assert build([["1", "2", "3"], ["4", "5", "6"]]) == r"(1|2|3)\s+?(4|5|6)"
    assert build([["1", "2", "3"], RegexVariative.Any, "abyr"]) == r"(1|2|3)(.*)(abyr)"

    assert build([["зайч~", "мальчик"]]) == r"(зайч\w.|мальчик)"

    assert build(["cat", RegexVariative.Any]) == r"(cat)(.*)"
    assert build(["cat", RegexVariative.Any, "dog"]) == r"(cat)(.*)(dog)"
    assert build([RegexVariative.Any, "dog"]) == r"(.*)(dog)"


def test_rabbit():
    args = [
        ["1", "2", "3"],
        "вышел",
        ["зайч~", "маль~"],
    ]

    rv = RegexVariative(args)
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
        RegexVariative.Any,
    ]

    rv = RegexVariative(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("cat"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 3, 0.5)


def test_star_merge():
    args = [
        "cat",
        RegexVariative.Any,
    ]

    rv = RegexVariative(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("cat"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 3, 1.5)


def test_weighted_rabbit():
    args = [
        RegexVariative.Weighted(["1", "2", "3"]),
        RegexVariative.Weighted("вышел", weight=2),
        RegexVariative.Weighted(["зайч~", "маль~"]),
    ]

    rv = RegexVariative(args)
    inter = Interactivity()

    resp = asyncio.get_event_loop().run_until_complete(rv.eval(UserMessage("1 вышел зайчик"), Context(), inter))
    assert len(resp.value.value) == 1
    assert len(resp.value.value[0].ranges) == 1
    assert resp.value.value[0].ranges[0] == MatchRange(0, 14, 4)


if __name__ == "__main__":
    pytest.main(["-s", "-x", __file__])
