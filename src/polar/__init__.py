import random
import re
from abc import abstractmethod
from typing import List, Optional, Union

from frozendict import frozendict


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


class BaseIO:
    @abstractmethod
    async def read_event(self) -> Event:
        pass

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


class EvalResult:
    def __init__(self, state=CommandResult.OK, value=None):
        self.state: int = state
        self.value = value

    def merge_match_result(self, result: "EvalResult", is_conditions: bool):
        """
        Merge result with other
        For conditions we use other types
        :param result:
        :param is_conditions:
        :return:
        """

        if self.value is None:
            self.value = ListN([])

        if result and result.value is not None:
            if is_conditions:
                if isinstance(result.value, MatchResult):
                    self.value.value.append(result.value)

                if isinstance(result.value, ListN) and all(isinstance(m, MatchResult) for m in result.value.value):
                    self.value.value.extend(result.value.value)

            else:
                if isinstance(result.value, OutMessageEvent):
                    self.value.value.append(result.value)

                if isinstance(result.value, ListN): #and all(isinstance(m, OutMessageEvent) for m in result.value.value):
                    self.value.value.extend(result.value.value)


class AstNode:
    def __init__(self, is_condition=False, types=None):
        self.is_condition = is_condition
        self.types = types

    @abstractmethod
    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        pass

    def __repr__(self):
        return "ast:" + str(type(self)) + str(self.__dict__)


class MatchResult(AstNode):
    def __init__(self):
        self.ranges: List[MatchRange] = []

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        pass


class Condition(AstNode):
    def __init__(self, *condition):
        self.condition = condition

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        pass


class BreakAstNode(AstNode):
    pass


class ExitAstNode(AstNode):
    pass


class Regexp(AstNode):
    def __init__(self, regexps):
        super().__init__(is_condition=True)
        self.regexps = regexps

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        if not isinstance(event, UserMessage):
            return None

        values: List[MatchResult] = []

        for regexp in self.regexps:
            m = re.search(regexp, event.text)
            if m:
                start, end = m.start(0), m.end(0)

                match_result = MatchResult()
                if start != -1 and end != -1:
                    match_result.ranges.append(MatchRange(start, end))
                values.append(match_result)

        return EvalResult(value=ListN(values)) if values else None


class SimpleResponse(AstNode):
    def __init__(self, responses):
        super().__init__()
        self.responses = responses

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        async def _eval(part):
            if isinstance(part, str):
                return OutMessageEvent(part)
            else:
                return await part.eval(event, context)

        random.seed(context["random_seed"])
        part = random.choice(self.responses)
        if isinstance(part, OutMessageEvent):
            part = [await _eval(p) for p in part.parts]

        if isinstance(part, str):
            part = OutMessageEvent(part)

        return EvalResult(value=ListN(part))


class Set(AstNode):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        context[self.name] = self.value
        await context.commit()

        return None


class Anchor:
    def __init__(self, word, offset):
        self.word = word
        self.offset = offset


class ListN(AstNode):
    def __init__(self, value):
        if not isinstance(value, list):
            raise RuntimeError("Must be list: %s" % value)
        self.value = value

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        return None


class AnchorFeature(AstNode):
    def __init__(self, *, var, anchors):
        super().__init__(types=UserMessage)
        self.var = var
        self.anchors = anchors

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        if not isinstance(event, UserMessage):
            return None

        words = event.text.split(" ")

        results = []

        for word_idx, word in enumerate(words):
            for anchor in self.anchors:
                if word.lower() != anchor.word.lower():
                    continue

                if anchor.offset < 0:
                    left = word_idx + anchor.offset
                    right = word_idx
                else:
                    left = word_idx + 1
                    right = word_idx + 1 + anchor.offset

                match = words[left : right]
                # if self.var is not None:
                #     context[self.var] = match
                #     await context.commit()

                if not match:
                    continue

                results.append({
                    "idx": word_idx,
                    "offset": anchor.offset,
                    "match": match,
                })

        return EvalResult(value=ListN(results))


class NameFeature(AstNode):
    weight = 2

    def __init__(self, vocab, var):
        super().__init__()
        self.vocab = vocab
        self.var = var
        anchors = [
            Anchor("я", 1),
            Anchor("я", -1),
            Anchor("меня", 1),
            Anchor("меня", -1),
            Anchor("зовут", -1),
            Anchor("зовут", +1),
            Anchor("имя", -1),
            Anchor("имя", +1),
        ]
        self.anchor = AnchorFeature(anchors=anchors, var=None)

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        results = await self.anchor.eval(event, None)
        if results is None:
            return None

        if not isinstance(results.value, ListN):
            raise RuntimeError("Anchor object returned not list or none")

        anchor_results = results.value.value

        values: List[MatchResult] = []

        for res in anchor_results:
            vocab_entry = self.vocab.get(res["match"][0].lower())
            if not vocab_entry:
                continue
            context[self.var] = vocab_entry["norm"]
            # Context
            values.append(MatchResult())

        return EvalResult(value=ListN(values)) if values else None


class If(AstNode):
    def __init__(self, if_, then_, else_=None):
        super().__init__()
        self.if_ = if_
        self.then_ = then_
        self.else_ = else_

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        resp = await self.if_.eval(event, context)
        if resp.value:
            resp = await self.then_.eval(event, context)
        elif self.else_ is not None:
            resp = await self.else_.eval(event, context)

        return resp


class Print(AstNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def eval(self, message: Event, context: Context) -> Optional[EvalResult]:
        return EvalResult(value=OutMessageEvent(context.get(self.name, "")))


class Empty(AstNode):
    def __init__(self, var):
        self.var = var

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        return EvalResult(value=not bool(context.get(self.var)))


class NotEmpty(AstNode):
    def __init__(self, var):
        self.var = var

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        return EvalResult(value=bool(context.get(self.var)))


class RegexVariative(AstNode):

    class Any:
        pass

    class Weighted:
        weighted = 1.

    def __init__(self, args):
        super().__init__()
        self.args = args
        self._re = self._compile_re(self._build_re(self.args))

    @staticmethod
    def _format_word(word):
        if word.endswith("~"):
            word = word[:-1] + r"\w."
        return word

    @classmethod
    def _build_re(cls, args):
        r = ""
        for arg in args:
            if isinstance(arg, list):
                vars = "|".join(cls._format_word(w) for w in arg)
                r += f"({vars})"
            elif arg == RegexVariative.Any or isinstance(arg, RegexVariative.Any):
                r += ".*"
            elif isinstance(arg, str):
                r += cls._format_word(arg)

            r += " "

        return r.rstrip()

    @staticmethod
    def _compile_re(r):
        return re.compile(r, flags=re.MULTILINE | re.IGNORECASE)

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        if not isinstance(event, UserMessage):
            return None

        m = re.search(self._re, event.text)
        value = None
        if m:
            match_result = MatchResult()
            match_result.ranges.append(MatchRange(m.start(0), m.end(0)))
            value = ListN([match_result])
        return EvalResult(state=CommandResult.OK, value=value)


class Flow(AstNode):
    def __init__(self, commands, is_conditions=False):
        self.commands = commands
        self.is_conditions = is_conditions

    async def eval(self, event: Event, context: Context) -> Optional[EvalResult]:
        result = EvalResult()

        for command in self.commands:
            res = await self._eval_command(command, event, context)

            result.merge_match_result(res, is_conditions=self.is_conditions)

            if res and res.state in (CommandResult.EXIT, CommandResult.BREAK):
                return result

        return result

    async def _eval_command(self, command: AstNode, event: Event, context: Context) -> Optional[EvalResult]:
        if isinstance(command, BreakAstNode):
            return EvalResult(state=CommandResult.BREAK)

        if isinstance(command, ExitAstNode):
            return EvalResult(state=CommandResult.EXIT)

        resp = await command.eval(event, context)

        if command.is_condition:
            if not resp:
                return EvalResult(state=CommandResult.BREAK)

        return resp


class Rule:
    def __init__(self, *, name=None, weight=1):
        self.name = name
        self.weight = weight
        self.condition = Flow([], is_conditions=True)
        self.flow = Flow([])


class Bot:
    def __init__(self):
        self.rules: List[Rule] = []

    def add_rules(self, rules):
        self.rules.extend(rules)


class ConsoleIO(BaseIO):
    async def read_event(self) -> Event:
        text = input("<--")
        msg = UserMessage(text)
        return msg

    async def send_event(self, event: Event):
        if not isinstance(event, OutMessageEvent):
            raise RuntimeError("Event %s is not OutMessageEvent" % event)
        print("-->", event.parts)


class Executor:
    async def execute_event(self, event: Event, bot: Bot, context: Context):
        matched_results = []

        for rule_idx, rule in enumerate(bot.rules):
            resp = await rule.condition.eval(event, context)
            if resp is None or resp.value is None:
                continue

            if isinstance(resp.value, ListN) and not resp.value.value:
                continue

            # Merge MatchResult(s) and store in all results

            if isinstance(resp.value, MatchResult):
                matched_results.append((rule_idx, resp))
            elif isinstance(resp.value, ListN) and all(isinstance(m, MatchResult) for m in resp.value.value):
                matched_results.extend([(rule_idx, r) for r in resp.value.value])
            else:
                raise RuntimeError("Response %s is not MatchResult or List[MatchResult]" % resp.value)

        if not matched_results:
            return None

        # TODO: Sort by and peek suitable results to evaluate. Currently first
        best_response = matched_results[0]
        rule_idx, match = best_response
        rule = bot.rules[rule_idx]

        response = await rule.flow.eval(event, context)

        if response.value:
            return response.value.value
        else:
            return None

    async def loop(self, *, bot: Bot, context: Context, io: BaseIO):
        while True:
            event = await io.read_event()

            response_events = await self.execute_event(event, bot, context)

            if response_events:
                for response_event in response_events:
                    await io.send_event(response_event)
            else:
                pass  # Log it too
