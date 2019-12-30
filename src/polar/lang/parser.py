import html
import itertools
from typing import List

from bs4 import BeautifulSoup

from polar.lang import OutMessageEvent
from polar.lang.all import SimpleResponse
from polar.lang.eval import Bot, Rule
from polar.lang.regex_rule import RegexRule


def _transform_template_text(text):
    text = text.replace("<br>", "\n")
    soup = BeautifulSoup(text, "html.parser")

    for div in soup.find_all("div"):
        continue_prev_line = False
        div.replace_with(("" if continue_prev_line else "\n") + div.text)

    out_text = soup.text.strip()
    out_text2 = html.unescape(out_text)
    return out_text2


class ArmBotParser:
    def __init__(self):
        pass

    def load_bot(self, templates):
        bot = Bot()

        rules = self.parse_rules(templates)
        bot.rules.extend(rules)

        return bot

    @classmethod
    def parse_rules(cls, templates) -> List[Rule]:
        rules = []

        for template in templates:
            rule = cls.parse_rule(template)
            rules.append(rule)
        return rules

    @classmethod
    def parse_rule(cls, template):
        content = _transform_template_text(template["content"])

        ST_RULE = 0
        ST_OUT = 1
        state = ST_RULE

        conditions = []
        simple_responses = []

        for line in content.split("\n"):
            sline = line.lstrip()

            if sline.startswith("//"):
                # comment line
                continue

            if state == ST_RULE:
                if sline.startswith("$"):
                    cmd = sline[1:].lstrip()

                    items = cmd.split()

                    build_items = []

                    for item in items:
                        if item == "*":
                            add = RegexRule.Any
                        else:
                            add = item
                        build_items.append(add)

                    conditions.append(RegexRule(build_items))

                elif sline.startswith("#"):
                    cmd = sline[1:].lstrip()
                    simple_responses.append(OutMessageEvent(cmd))
                    state = ST_OUT

            elif state == ST_OUT:
                if sline.startswith("#"):
                    cmd = sline[1:].lstrip()
                    simple_responses.append(OutMessageEvent(cmd))


        rule = Rule(name=template["id"])
        rule.condition.commands.extend(conditions)
        rule.flow.commands.extend([SimpleResponse(simple_responses)])

        return rule
