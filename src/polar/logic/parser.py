import html
import itertools
from typing import List

from bs4 import BeautifulSoup

from polar import Bot, Rule, RegexVariative, OutMessageEvent, SimpleResponse


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
        flow = []
        simple_responses = []

        for line in content.split("\n"):
            sline = line.lstrip()

            if sline.startswith("//"):
                # comment line
                continue

            if state == ST_RULE:
                if sline.startswith("$"):
                    cmd = sline[1:].lstrip()

                    # Replace * for Any object and split to list magic shit
                    anys = cmd.split("*")

                    x = [x.strip() for x in anys]

                    # Insert back Any after every object. Skip last
                    y = list(itertools.chain(*itertools.product(x, [RegexVariative.Any])))[:-1]

                    # Remove empties
                    z = [x for x in y if x]
                    conditions.append(RegexVariative(z))

                elif sline.startswith("#"):
                    cmd = sline[1:].lstrip()
                    simple_responses.append(OutMessageEvent(cmd))
                    state = ST_OUT

            if state == ST_OUT:
                if sline.startswith("#"):
                    cmd = sline[1:].lstrip()


        rule = Rule(name=template["id"])
        rule.condition.commands.extend(conditions)
        rule.flow.commands.extend([SimpleResponse(simple_responses)])

        return rule
