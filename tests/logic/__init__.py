import asyncio
from typing import List

from polar.lang import UserMessage, Context, Event
from polar.lang.eval import Bot, Executor, ExecutorState
from tests.common import LogInteractivity


def execute_event(event: UserMessage, bot: Bot, *, context=None, executor=None) -> (List[Event], ExecutorState):
    context = context or Context({
        "random_seed": 123,
    })
    executor = executor or Executor()

    inter = LogInteractivity()
    executor_state = asyncio.get_event_loop().run_until_complete(
        executor.execute_event(event=event, bot=bot, context=context, inter=inter))

    return inter.events, executor_state
