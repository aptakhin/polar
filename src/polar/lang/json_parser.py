from polar.lang.eval import Bot
from polar.lang.json_import import load_bot_rule_content


class JsonBotParser:
    def __init__(self):
        pass

    def load_bot(self, templates):
        bot = Bot()

        for template in templates:
            print("Loading", template["id"], template["content"])
            result = load_bot_rule_content(bot, template["content"])
            if result:
                print("Error", template["id"], result)

        return bot
