import json
import os
import subprocess

import sys
from functools import wraps

from polar.lang import TermNode, RuleNode, AstNode
from polar.lang.all import Flow, SimpleResponse, CallNode
from polar.lang.eval import Bot, Rule
from polar.lang.regex_rule import RegexRule

_node_creators = {}

def creates(name):
    def foo(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # TODO: trace in-depth calls
            return f(*args, **kwargs)

        _node_creators[name] = f

        return wrapper

    return foo


@creates("flow")
def flow(js):
    commands = [_load_node(command) for command in js["flow"]]
    return Flow(commands)


@creates("rule")
def response(js):
    commands = [_load_node(command) for command in js["args"]]
    return RuleNode(commands)


@creates("response")
def response(js):
    commands = [_load_node(command) for command in js["args"]]
    return SimpleResponse(commands)


@creates("term")
def term(js):
    return TermNode(js["value"])


@creates("call")
def call(js):
    args = [_load_node(arg) for arg in js["args"]]
    return CallNode(args)


@creates("regexp_rule")
def regexp_rule(js):
    def _load_arg(arg_js):
        node = _load_node(arg_js)
        if not isinstance(node, TermNode):
            raise RuntimeError("Currently only str term supported "
                               "in RegexRule loader!")

        value = arg_js["value"]
        if arg_js["type"] == "kleine":
            value = RegexRule.Any

        return value

    args = [_load_arg(arg) for arg in js["args"]]
    return RegexRule(args)


def _load_node(js):
    if not js.get("node"):
        raise RuntimeError("No node given in object `%s`!" % js)

    if js["node"] not in _node_creators:
        raise RuntimeError("No registered loader for `%s` node!" % js["node"])

    obj = _node_creators[js["node"]](js)
    return obj


def load(js: dict) -> AstNode:
    return _load_node(js)


def load_bot_rule(bot: Bot, js: dict):
    rule_all_flow = load(js)

    if not isinstance(rule_all_flow, Flow):
        raise RuntimeError("Not Flow in loading bot!")

    simple_responses = []

    rule = Rule()
    for command in rule_all_flow.commands:
        if isinstance(command, RuleNode):
            rule.condition.commands.append(command)
        else:
            simple_responses.extend(command.responses)

    rule.flow.commands.append(SimpleResponse(simple_responses))

    bot.add_rule(rule)


def load_bot_rule_content(bot: Bot, content: str):
    POLAR_PARSER_EXECUTABLE = os.getenv("POLAR_PARSER_EXECUTABLE")
    if not POLAR_PARSER_EXECUTABLE:
        raise RuntimeError("No polar-parser given!")

    polar_parser_call = subprocess.Popen([POLAR_PARSER_EXECUTABLE],
                                         stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE)
    stdout, stderr = polar_parser_call.communicate(content.encode())

    data = stdout.decode()
    if not data:
        return "Empty data from polar-server"

    js = json.loads(data)

    load_bot_rule(bot, js)


if __name__ == "__main__":
    v = load(json.load(sys.stdin))
    p = 0
