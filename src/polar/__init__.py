import abc
import asyncio
import random
import re


class Context(dict):
    async def commit(self):
        print("COMMITED")


class UserMessage:
    def __init__(self, text):
        self.text = text


class OutMessage:
    def __init__(self, parts=None):
        if not isinstance(parts, list):
            parts = [parts]

        self.parts = parts

    def __str__(self):
        return str(self.parts)

    def __repr__(self):
        return "OutMessage(%s)" % repr(self.parts)


class BaseIO:
    @abc.abstractmethod
    async def read_message(self) -> UserMessage:
        pass

    @abc.abstractmethod
    async def send_message(self, message: OutMessage):
        pass


class Response:
    def __init__(self):
        pass

    @abc.abstractmethod
    async def add_part(self, part: OutMessage, context: Context):
        pass

    @abc.abstractmethod
    async def send(self):
        pass


class CombinedResponse(Response):
    def __init__(self, io: BaseIO):
        self.parts = []
        self.io = io

    async def add_part(self, out: OutMessage, context: Context):
        for part in out.parts:
            if isinstance(part, dict):
                if part["type"] == "var":
                    self.parts.append(context.get(part["name"], ""))
                else:
                    self.parts.append(part)
            else:
                self.parts.append(part)

    async def send(self):
        # parts = []
        # for p in self.parts:
        #     parts.extend(p.parts)

        message = OutMessage(parts=self.parts)

        await self.io.send_message(message)


class Command:
    def __init__(self, is_condition=False):
        self.is_condition = is_condition

    @abc.abstractmethod
    async def eval(self, message: UserMessage, context: Context, resp: Response):
        pass


class Condition(Command):
    def __init__(self, *condition):
        self.condition = condition

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        pass


class BreakCommand(Command):
    pass


class ExitCommand(Command):
    pass


class Regexp(Command):
    def __init__(self, regexps):
        super().__init__(is_condition=True)
        self.regexps = regexps

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        for regexp in self.regexps:
            m = re.search(regexp, message.text)
            if m:
                return True

        return False


class SimpleResponse(Command):
    def __init__(self, responses):
        super().__init__()
        self.responses = responses

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        part = random.choice(self.responses)
        await resp.add_part(part, context)
        return True


class Set(Command):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        context[self.name] = self.value
        await context.commit()
        return True


class Anchor:
    def __init__(self, word, offset):
        self.word = word
        self.offset = offset


class AnchorFeature(Command):
    def __init__(self, *, var, anchors):
        self.var = var
        self.anchors = anchors

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        words = message.text.split(" ")

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
                if self.var is not None:
                    context[self.var] = match
                    await context.commit()

                if not match:
                    continue

                results.append({
                    "idx": word_idx,
                    "offset": anchor.offset,
                    "match": match,
                })

        return results


class NameFeature(Command):
    def __init__(self, vocab, var):
        super().__init__()
        self.vocab = vocab
        self.var = var
        anchors = [
            Anchor("меня", 1),
            Anchor("меня", -1),
            Anchor("зовут", -1),
            Anchor("зовут", +1),
        ]
        self.anchor = AnchorFeature(anchors=anchors, var=None)

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        results = await self.anchor.eval(message, None, None)
        for res in results:
            vocab_entry = self.vocab.get(res["match"][0].lower())
            if vocab_entry:
                context[self.var] = vocab_entry["norm"]
                return True

        return False

class CommandResult:
    OK = 0
    ERROR = 2
    BREAK = 3
    EXIT = 4

    def __init__(self, state):
        self.state = state
        self.result = {}


class If(Command):
    def __init__(self, if_, then_, else_=None):
        super().__init__()
        self.if_ = if_
        self.then_ = then_
        self.else_ = else_

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        if await self.if_.eval(message, context, resp):
            res = await self.then_.eval(message, context, resp)
        elif self.else_ is not None:
            res = await self.else_.eval(message, context, resp)

        return res


class NotEmpty(Command):
    def __init__(self, var):
        self.var = var

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        return bool(context.get(self.var))


class Flow(Command):
    def __init__(self, commands):
        self.commands = commands

    async def eval(self, message: UserMessage, context: Context, resp: Response):
        for command in self.commands:
            res = await self._eval_command(command, message, context, resp)

            if res.state in (CommandResult.EXIT, CommandResult.BREAK):
                return res

        return CommandResult(state=CommandResult.OK)

    async def _eval_command(self, command: Command, message: UserMessage, context: Context, resp: Response):
        if isinstance(command, BreakCommand):
            return CommandResult(state=CommandResult.BREAK)

        if isinstance(command, ExitCommand):
            return CommandResult(state=CommandResult.EXIT)

        res = await command.eval(message, context, resp)

        if command.is_condition:
            if not res:
                return CommandResult(state=CommandResult.BREAK)

        return CommandResult(state=CommandResult.OK)


class Rule:
    def __init__(self, *, name, order):
        self.name = name
        self.order = order
        self.flow = Flow([])


class Bot:
    def __init__(self):
        self.rules = []

    def add_rules(self, rules):
        self.rules.extend(rules)
        self.rules.sort(key=lambda rule: rule.order)


class ConsoleIO(BaseIO):
    async def read_message(self) -> UserMessage:
        text = input("<--")
        msg = UserMessage(text)
        return msg

    async def send_message(self, message: OutMessage):
        print("-->", message.parts)


class _ExecutorResult:
    OK = 0
    ERROR = 2
    BREAK = 3
    EXIT = 4

    def __init__(self, state):
        self.state = state
        self.result = {}


class Executor:
    async def loop(self, *, bot: Bot, context: Context, io: BaseIO):
        while True:
            message = await io.read_message()

            resp = CombinedResponse(io=io)

            for rule in bot.rules:
                res = await rule.flow.eval(message, context, resp)

                if res.state == CommandResult.EXIT:
                    break

            await resp.send()



async def test_anchor():
    anchors = [
        Anchor("в", +1),
        Anchor("во", +1),
    ]
    feat = AnchorFeature(anchors=anchors, var=None)
    context = Context()
    res = await feat.eval(UserMessage("во Владивосток"), context=context, resp=Response())
    assert len(res) == 1
    assert res[0]["idx"] == 0
    assert res[0]["match"] == ["Владивосток"]

    anchors = [
        Anchor("меня", 1),
        Anchor("меня", -1),
        Anchor("зовут", -1),
        Anchor("зовут", +1),
    ]
    feat = AnchorFeature(anchors=anchors, var=None)
    context = Context()
    res = await feat.eval(UserMessage("Сашей меня зовут все"), context=context, resp=Response())
    # assert context[var] == ["Сашей"]
    p = 0


def test():
    asyncio.get_event_loop().run_until_complete(test_anchor())

    bot = Bot()

    rule_hi_stop = Rule(name="name", order=0)
    rule_hi_stop.flow = Flow([
        Regexp(["привет_как_дела"]),
        SimpleResponse([OutMessage("И_тебе_привет")]),
        Set("secret", "1"),
        ExitCommand(),
    ])

    rule_hi = Rule(name="name", order=1)
    rule_hi.flow = Flow([
        Regexp(["привет", "прив"]),
        If(NotEmpty("name"), then_=Flow([
            SimpleResponse([OutMessage(["Привет, ", {"type": "var", "name": "name"}, "!"])]),
        ]), else_=Flow([
            SimpleResponse([OutMessage("И тебе привет"), OutMessage("Приветище!")]),
        ]),
       )
    ])

    rule_mind = Rule(name="name", order=2)
    rule_mind.flow = Flow([
        Regexp(["как дела", "дела"]),
        SimpleResponse([OutMessage("Дела супер!"), OutMessage("Дела отлично!")]),
    ])

    vocab = {
        "сашей": {"norm": "Саша"},
        "машей": {"norm": "Маша"},
    }

    rule_name = Rule(name="name", order=-1)
    rule_name.flow = Flow([
        NameFeature(vocab=vocab, var="name"),
    ])

    bot.add_rules([rule_name, rule_hi_stop, rule_hi, rule_mind])

    console_io = ConsoleIO()
    context = Context()
    executor = Executor()

    asyncio.get_event_loop().run_until_complete(executor.loop(bot=bot, context=context, io=console_io))


if __name__ == "__main__":
    test()
