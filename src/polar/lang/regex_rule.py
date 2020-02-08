import re
from typing import Optional, Union

from polar.lang import PolarInternalError, ListN, AstNode, \
    PolarInvalidArguments, EvalResult, MatchResult, Event, \
    Context, Interactivity, UserMessage, MatchRange, CommandResult


class RegexRule(AstNode):
    """
    Most useful rule for matching text with set of regexes.
    Evaluetes with weights.
    """

    ANY_WEIGHT = 0.01

    class Any:
        pass

    class Node:
        def __init__(self, arg, weight: Union[int, float]=None):
            self._validate_arg(arg)
            self._arg = arg
            self._weight = weight

        @property
        def arg(self):
            return self._arg

        @property
        def weight(self):
            return self._weight

        def __eq__(self, other: "Node"):
            if type(self) != type(other):
                return False
            return self.arg == other.arg and self.weight == other.weight

        def __repr__(self):
            return "Node(%s, %s)" % (repr(self.arg), repr(self.weight))

        def build_re(self):
            if isinstance(self.arg, list):
                vars = "|".join(self._format_word(w) for w in self.arg)
                r = f"({vars})"
            elif self.arg == RegexRule.Any:
                r = "(.*)"
            elif isinstance(self.arg, str):
                r = f"({self._format_word(self.arg)})"
            else:
                raise PolarInternalError("Unhandled build_re argument: %s %s" %
                                         (self.arg, type(self.arg)))

            return r

        @staticmethod
        def _format_word(word):
            if word.endswith("~"):
                word = word[:-1] + r"\w."
            return word

        @classmethod
        def _validate_arg(cls, arg):
            if arg == RegexRule.Any:
                pass
            elif isinstance(arg, list):
                all(cls._validate_arg(a) for a in arg)
            elif not isinstance(arg, str):
                raise PolarInvalidArguments("Arg in RegexVariative can be str, "
                                            "list of str or "
                                            "Got: %s %s" % (arg, type(arg)))

    def __init__(self, args):
        super().__init__()
        self._args = self._init_args(args)
        self._re = self._compile_re(self._build_re(self._args))

    @property
    def args(self):
        return self._args

    async def eval(self, event: Event, context: Context, inter: Interactivity) \
            -> Optional[EvalResult]:
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

    def build_re(self):
        return self._build_re(self.args)

    @classmethod
    def _init_args(cls, args):
        return [
                   (arg if isinstance(arg, cls.Node) else cls.Node(arg))
            for arg in args
        ]

    @classmethod
    def _is_any_arg(cls, arg):
        return arg == cls.Any or isinstance(arg, cls.Node) \
               and arg.arg == cls.Any

    @classmethod
    def _build_re(cls, args):
        built_args = [arg.build_re() for arg in args]

        idx = 0
        r = r""
        while idx < len(built_args):
            if idx > 0 and not cls._is_any_arg(args[idx]) and \
                           not cls._is_any_arg(args[idx - 1]):
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
                    # Small penalty for non-matching * made for case
                    # when exact match will be better
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

