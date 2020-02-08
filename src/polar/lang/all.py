import asyncio
import random
import re
from typing import List, Optional

from polar.lang import AstNode, Event, Context, UserMessage, MatchResult, \
    Interactivity, EvalResult, MatchRange, ListN, \
    OutMessageEvent, CommandResult, TermNode


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

        # random.seed(context["random_seed"])
        part = random.choice(self.responses)
        if isinstance(part, OutMessageEvent):
            part = [await _eval(p) for p in part.parts]

        if isinstance(part, str):
            part = [OutMessageEvent(part)]

        if isinstance(part, TermNode):
            part = [OutMessageEvent(part.value)]

        for p in part:
            value = p
            if isinstance(p, TermNode):
                value = p.value
            await inter.send_event(value)

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


class CallNode(AstNode):
    def __init__(self, args):
        super().__init__()
        self.args = args

    async def eval(self, message: Event, context: Context, inter: Interactivity) -> Optional[EvalResult]:
        print("CallFunc", self.args)
        return EvalResult(value=[])


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
