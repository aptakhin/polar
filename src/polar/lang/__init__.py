from abc import abstractmethod
from typing import Union, List, Optional
from frozendict import frozendict


class PolarInvalidArguments(ValueError):
    pass


class PolarInternalError(RuntimeError):
    pass


class Context(frozendict):
    pass


class Event:
    pass


class UserMessage(Event):
    def __init__(self, text):
        self.text = text


class OutMessageEvent(Event):
    def __init__(self, parts=None):
        if not isinstance(parts, list):
            parts = [parts]

        self.parts = parts

    def __str__(self):
        return str(self.parts)

    def __repr__(self):
        return "OutMessageEvent(%s)" % repr(self.parts)


class Interactivity:
    @abstractmethod
    async def send_event(self, event: Event):
        pass


class CommandResult:
    OK = 0
    EXIT = 1
    ERROR = 2
    BREAK = 3

    def __init__(self, state):
        self.state = state
        self.result = {}


class MatchRange:
    def __init__(self, start: int, end: int, weight: Union[int, float]=1):
        self.start = start
        self.end = end
        self.weight = weight

    def __repr__(self):
        return "MatchRange(%s, %s, %s)" % (repr(self.start), repr(self.end), repr(self.weight))

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end and self.weight == other.weight

class AstNode:
    def __init__(self, is_condition=False, types=None):
        self.is_condition = is_condition
        self.types = types

    @abstractmethod
    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional["EvalResult"]:
        pass

    def __repr__(self):
        return "ast:" + str(type(self)) + str(self.__dict__)


class ListN(AstNode):
    def __init__(self, value):
        if not isinstance(value, list):
            raise RuntimeError("Must be list: %s" % value)
        self.value = value


class MatchResult(AstNode):
    def __init__(self):
        self.ranges: List[MatchRange] = []


class MatchResultEvent(Event):
    def __init__(self):
        self.ranges: List[MatchRange] = []


class EvalResult:
    def __init__(self, state=CommandResult.OK, value=None):
        self.state: int = state
        self.value = value

    def merge_match_result(self, result: "EvalResult"):
        """
        Merge result with other
        For conditions we use other types
        :param result:
        :return:
        """

        if self.value is None:
            self.value = ListN([])

        if result and result.value is not None:
            if isinstance(result.value, MatchResult):
                self.value.value.append(result.value)

            # FIXME: logic
            if isinstance(result.value, ListN):# and all(isinstance(m, MatchResult) for m in result.value.value):
                self.value.value.extend(result.value.value)
