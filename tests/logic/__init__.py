import asyncio

from polar import UserMessage, Context, Executor, Bot
from tests.common import LogInteractivity


def test_input(event: UserMessage, bot: Bot, *, context=None, executor=None):
    context = context or Context({
        "random_seed": 123,
    })
    executor = executor or Executor()

    inter = LogInteractivity()
    asyncio.get_event_loop().run_until_complete(
        executor.execute_event(event=event, bot=bot, context=context, inter=inter))

    return inter.events
