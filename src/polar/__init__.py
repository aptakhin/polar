import asyncio
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

            if isinstance(result.value, ListN) and all(isinstance(m, MatchResult) for m in result.value.value):
                self.value.value.extend(result.value.value)


class AstNode:
    def __init__(self, is_condition=False, types=None):
        self.is_condition = is_condition
        self.types = types

    @abstractmethod
    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        pass

    def __repr__(self):
        return "ast:" + str(type(self)) + str(self.__dict__)


class MatchResult(AstNode):
    def __init__(self):
        self.ranges: List[MatchRange] = []


class MatchResultEvent(Event):
    def __init__(self):
        self.ranges: List[MatchRange] = []



class Condition(AstNode):
    def __init__(self, *condition):
        self.condition = condition


class BreakAstNode(AstNode):
    pass


class ExitAstNode(AstNode):
    pass


class Regexp(AstNode):
    def __init__(self, regexps):
        super().__init__(is_condition=True)
        self.regexps = regexps

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
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

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
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
            part = [OutMessageEvent(part)]

        for p in part:
            await inter.send_event(p)

        return EvalResult(value=ListN(part))


class Set(AstNode):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
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


class AnchorFeature(AstNode):
    def __init__(self, *, var, anchors):
        super().__init__(types=UserMessage)
        self.var = var
        self.anchors = anchors

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
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

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
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
    def __init__(self, if_: AstNode, then_: AstNode, else_: Optional[AstNode]=None):
        super().__init__()
        self.if_ = if_
        self.then_ = then_
        self.else_ = else_

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        resp = await self.if_.eval(event, context, inter)
        if resp.value:
            resp = await self.then_.eval(event, context, inter)
        elif self.else_ is not None:
            resp = await self.else_.eval(event, context, inter)

        return resp


class Print(AstNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def eval(self, message: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        return EvalResult(value=OutMessageEvent(context.get(self.name, "")))


class Empty(AstNode):
    def __init__(self, var):
        self.var = var

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        return EvalResult(value=not bool(context.get(self.var)))


class NotEmpty(AstNode):
    def __init__(self, var):
        self.var = var

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        return EvalResult(value=bool(context.get(self.var)))


class Sleep(AstNode):
    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        await asyncio.sleep(self.seconds)
        return EvalResult()


class PolarInvalidArguments(ValueError):
    pass


class PolarInternalError(RuntimeError):
    pass


class RegexVariative(AstNode):

    class Any:
        pass

    class Weighted:
        def __init__(self, arg, weight: Union[int, float]=1):
            RegexVariative._validate_arg(arg)
            self.arg = arg
            self.weight = weight

    def __init__(self, args):
        super().__init__()
        self.args = args
        self._re = self._compile_re(self._build_re(self.args))

    @classmethod
    def _validate_arg(cls, arg):
        if isinstance(arg, cls.Weighted):
            cls._validate_arg(arg.arg)
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
        elif arg == RegexVariative.Any or isinstance(arg, RegexVariative.Any):
            r = "(.*)"
        elif isinstance(arg, str):
            r = f"({cls._format_word(arg)})"
        elif isinstance(arg, cls.Weighted):
            r = cls._build_arg(arg.arg)
        else:
            raise PolarInternalError("Unexpected argument: %s %s" % (arg, type(arg)))

        return r

    @classmethod
    def _is_any_arg(cls, arg):
        return arg == cls.Any or isinstance(arg, cls.Weighted) and arg.arg == cls.Any

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
        if isinstance(arg, cls.Weighted):
            return arg.weight
        elif arg == cls.Any:
            if m[0] == m[1]:
                # Small penalty for non-matching * made for case when exact match will be better
                return -0.03
            else:
                # Small bonus for * matching
                return 0.03
        else:
            return 1.

    def _calc_weight(self, match):
        match_regs = match.regs[1:]
        return sum(self._weight_arg(a, b) for a, b in zip(self.args, match_regs))

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


class Flow(AstNode):
    def __init__(self, commands):
        self.commands = commands

    async def eval(self, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        result = EvalResult()

        for command in self.commands:
            res = await self._eval_command(command, event, context, inter)

            result.merge_match_result(res)

            if res and res.state in (CommandResult.EXIT, CommandResult.BREAK):
                return result

        return result

    async def _eval_command(self, command: AstNode, event: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        if isinstance(command, BreakAstNode):
            return EvalResult(state=CommandResult.BREAK)

        if isinstance(command, ExitAstNode):
            return EvalResult(state=CommandResult.EXIT)

        resp = await command.eval(event, context, inter)

        if command.is_condition:
            if not resp:
                return EvalResult(state=CommandResult.BREAK)

        return resp


class Rule:
    def __init__(self, *, name=None, weight=1, condition=None, flow=None):
        self.name = name
        self.weight = weight
        self.condition = condition or Flow([])
        self.flow = flow or Flow([])


class Bot:
    def __init__(self):
        self.rules: List[Rule] = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def add_rules(self, rules):
        self.rules.extend(rules)


class ExecutorState:
    def __init__(self, sorted_results):
        self.sorted_results = sorted_results


class Executor:
    @classmethod
    async def execute_event(cls, event: Event, bot: Bot, context: Context, inter: Interactivity):
        matched_results = await cls._test_rules(event, bot, context)

        if not matched_results:
            return None

        def get_match_weight(match_result: MatchResult):
            return sum(m.weight for m in match_result.ranges)

        sorted_results = sorted(matched_results, key=lambda res: -get_match_weight(res[1]))

        # TODO: Peek suitable results to evaluate by range. Currently first best
        best_response = sorted_results[0]
        rule_idx, match = best_response
        rule = bot.rules[rule_idx]

        # We don't really care about result because all user output messages sent to inter instance
        _ = await rule.flow.eval(event, context, inter)

        return ExecutorState(
            sorted_results=sorted_results,
        )

    @classmethod
    async def _test_rules(cls, event: Event, bot: Bot, context: Context):
        matched_results = []

        dummy_inter = Interactivity()

        for rule_idx, rule in enumerate(bot.rules):
            resp = await rule.condition.eval(event, context, dummy_inter)
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

        return matched_results
