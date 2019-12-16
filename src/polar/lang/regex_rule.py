import re
from typing import Optional, Union

from polar.lang import PolarInternalError, ListN, AstNode, PolarInvalidArguments, EvalResult, MatchResult, Event, \
    Context, Interactivity, UserMessage, MatchRange, CommandResult


class RegexRule(AstNode):
    """
    Most useful rule for matching text with set of regexes.
    Evalues with weights.
    """

    ANY_WEIGHT = 0.01

    class Any:
        pass

    class Node:
        def __init__(self, arg, weight: Union[int, float]=None):
            RegexRule._validate_arg(arg)
            self._arg = arg
            self._weight = weight

        @property
        def arg(self):
            return self._arg

        @property
        def weight(self):
            return self._weight

    def __init__(self, args):
        super().__init__()
        self._args = self._init_args(args)
        self._re = self._compile_re(self._build_re(self._args))

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        if not isinstance(event, UserMessage):
            return None

        m = re.search(self._re, event.text)
        value = None
        if m:
            match_result = MatchResult()
            weight = self._calc_weight(m)
            match_result.ranges.append(MatchRange(m.start(0), m.end(0), weight))
            value = ListN([match_result])

        return EvalResult(state=CommandResult.OK, value=value)

    @classmethod
    def _init_args(cls, args):
        ret = []
        for arg in args:
            if isinstance(arg, cls.Node):
                add = arg
            else:
                add = cls.Node(arg)
            ret.append(add)
        return ret

    @classmethod
    def _validate_arg(cls, arg):
        if isinstance(arg, cls.Node):
            cls._validate_arg(arg.arg)
        elif arg == cls.Any:
            pass
        elif isinstance(arg, list):
            all(cls._validate_arg(a) for a in arg)
        elif not isinstance(arg, str):
            raise PolarInvalidArguments("Arg in RegexVariative can be str, list of str or "
                                        "Weighted from these. Got: %s %s" % (arg, type(arg)))

    @staticmethod
    def _format_word(word):
        if word.endswith("~"):
            word = word[:-1] + r"\w."
        return word

    @classmethod
    def _build_arg(cls, arg):
        if isinstance(arg, list):
            vars = "|".join(cls._format_word(w) for w in arg)
            r = f"({vars})"
        elif arg == RegexRule.Any or isinstance(arg, RegexRule.Any):
            r = "(.*)"
        elif isinstance(arg, str):
            r = f"({cls._format_word(arg)})"
        elif isinstance(arg, cls.Node):
            r = cls._build_arg(arg.arg)
        else:
            raise PolarInternalError("Unexpected argument: %s %s" % (arg, type(arg)))

        return r

    @classmethod
    def _is_any_arg(cls, arg):
        return arg == cls.Any or isinstance(arg, cls.Node) and arg.arg == cls.Any

    @classmethod
    def _build_re(cls, args):
        built_args = [cls._build_arg(arg) for arg in args]

        idx = 0
        r = r""
        while idx < len(built_args):
            if idx > 0 and not cls._is_any_arg(args[idx]) and not cls._is_any_arg(args[idx - 1]):
                r += r"\s+?"
            r += built_args[idx]

            idx += 1

        return r

    @staticmethod
    def _compile_re(r):
        return re.compile(r, flags=re.MULTILINE | re.IGNORECASE)

    @classmethod
    def _weight_arg(cls, arg, m):
        if isinstance(arg, cls.Node):
            if arg.arg == cls.Any and arg.weight is None:
                if m[0] == m[1]:
                    # Small penalty for non-matching * made for case when exact match will be better
                    return -cls.ANY_WEIGHT
                else:
                    # Small bonus for * matching
                    return cls.ANY_WEIGHT
            return arg.weight if arg.weight is not None else 1
        else:
            return 1.

    def _calc_weight(self, match):
        match_ranges = match.regs[1:]
        return sum(self._weight_arg(arg, match_range)
                   for arg, match_range in zip(self._args, match_ranges))

