from typing import List

from polar.lang import Event, Context, Interactivity, MatchResult, ListN
from polar.lang.all import Flow


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
    async def execute_event(cls, event: Event, bot: Bot, context: Context, inter: Interactivity) -> ExecutorState:
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
