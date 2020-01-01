import asyncio
import itertools

import asyncpg

from polar.proxy import proxy_conf

WORDS = """
alligator
ant
bear
bee
bird
camel
cat
cheetah
chicken
chimpanzee
cow
crocodile
deer
dog
dolphin
duck
eagle
elephant
fish
fly
fox
frog
giraffe
goat
goldfish
hamster
hippopotamus
horse
kangaroo
kitten
lion
lobster
monkey
octopus
owl
panda
pig
puppy
rabbit
rat
scorpion
seal
shark
sheep
snail
snake
spider
squirrel
tiger
turtle
wolf
zebra
accelerator
battery
blinker
brake
bumper
clutch
dashboard
gear
headlight
horn
hubcap
license plate
rearview mirror
seat
speedometer
taillight
tire
trunk
turn signal
wheel
windshield
windshield wiper
blackboard
blackboard eraser
book
bookcase
bulletin board
calendar
chair
chalk
clock
computer
desk
dictionary
eraser
map
notebook
pen
pencil
pencil sharpener
textbook
white board
one
two
three
four
five
six
seven
eight
nine
ten
eleven
twelve
thirteen
fourteen
fifteen
sixteen
seventeen
eighteen
nineteen
twenty
back
cheeks
chest
chin
ears
eyebrows
eyes
feet
fingers
foot
forehead
hair
hands
head
hips
knees
legs
lips
mouth
neck
nose
shoulders
stomach
teeth
teeth
throat
toes
tongue
tooth
waist
account
bills
borrow
alarm
cash
cashier
check
coins
credit
credit card
currency
customer
deposit
interest
lend
loan
manager
money
mortgage
pay
save
savings
guard
teller
vault
withdraw
angry
beautiful
brave
careful
careless
clever
crazy
cute
dangerous
exciting
famous
friendly
happy
interesting
lucky
old
poor
popular
rich
sad
thin
ugly
unlucky
young
after
always
before
during
lately
never
often
rarely
recently
sometimes
soon
today
tomorrow
usually
yesterday
""".strip().split()

async def load():
    db = await asyncpg.create_pool(dsn=proxy_conf.LOGIC_POSTGRES_DSN)
    async with db.acquire() as connection:
        profile_id = "13f46597-c964-460e-97d5-101079891e73"
        suite_id = "66fd1dc4-f276-416f-827d-f0dc34ff1291"

        await connection.execute("""
            DELETE FROM "public"."templates" WHERE suite_id=$1
         """, suite_id)

        result = await connection.execute("""
            INSERT INTO "public"."templates" ("suite_id", "created", "version", "position", "state", "content", "is_enabled", "is_compilable", "meta") VALUES ($1, NOW(), '1', $2, 'active', $3, 't', 't', '{}')
        """, suite_id, 0, "$ *\n# Don't understand")

        global WORDS
        words = WORDS
        WORDS = words[:40]

        for cnt, word in enumerate(WORDS, 1):
            content = f"$ {word}\n# exact: {word}\n"
            position = cnt
            result = await connection.execute("""
                INSERT INTO "public"."templates" ("suite_id", "created", "version", "position", "state", "content", "is_enabled", "is_compilable", "meta") VALUES ($1, NOW(), '1', $2, 'active', $3, 't', 't', '{}')
            """, suite_id, position, content)

        for cnt, word in enumerate(WORDS, 1):
            content = f"$ * {word} * \n# something with: {word}\n"
            position = cnt
            result = await connection.execute("""
                INSERT INTO "public"."templates" ("suite_id", "created", "version", "position", "state", "content", "is_enabled", "is_compilable", "meta") VALUES ($1, NOW(), '1', $2, 'active', $3, 't', 't', '{}')
            """, suite_id, position, content)

        for cnt, (w1, w2) in enumerate(itertools.product(WORDS, WORDS)):
            content = f"$ * {w1} * {w2} *\n# something with 2 words: {w1}, {w2}\n"
            position = cnt
            result = await connection.execute("""
                INSERT INTO "public"."templates" ("suite_id", "created", "version", "position", "state", "content", "is_enabled", "is_compilable", "meta") VALUES ($1, NOW(), '1', $2, 'active', $3, 't', 't', '{}')
            """, suite_id, position, content)
        return result


if __name__ == "__main__":
    db = asyncio.get_event_loop().run_until_complete(load())
