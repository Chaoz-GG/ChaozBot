import json
import random
import string
from datetime import date

import discord


# Parse list items into embed fields
def make_list_embed(fields, colour):
    embed = discord.Embed(colour=colour)

    for key, value in fields.items():
        embed.add_field(name=key, value=value, inline=True)

    return embed


# Generate a 10-letter random string of letters and digits
def generate_token():
    return '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


# Parse the cooldown time into a readable format
def parse_cooldown(cooldown):
    hours, remainder = divmod(int(cooldown), 3600)
    minutes, seconds = divmod(remainder, 60)

    return minutes, seconds


# Log a message in the log channel
async def log_message(ctx: discord.Interaction, message: str):
    with open('config.json') as json_file:
        data = json.load(json_file)
        log_channel_id = data['log_channel_id']

    log_channel = ctx.guild.get_channel(log_channel_id)

    return await log_channel.send(message)


def pad(line, limit):
    return line + " " * (limit-len(line))


def split_string(text, limit, sep=" "):
    words = text.split()

    if max(map(len, words)) > limit:
        raise ValueError("limit is too small")

    res = []
    part = words[0]
    others = words[1:]

    for word in others:
        if len(sep)+len(word) > limit-len(part):
            res.append(part)
            part = word

        else:
            part += sep + word

    if part:
        res.append(part)

    result = [pad(l, limit) for l in res]

    return result


# Calculate user age from birthday `datetime` object
def calculate_age(birthdate: date):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
