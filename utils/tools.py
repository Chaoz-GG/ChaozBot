#!/usr/bin/python3

import discord

import random
import string


def make_list_embed(fields):
    embed = discord.Embed()
    for key, value in fields.items():
        embed.add_field(name=key, value=value, inline=True)
    return embed


def generate_token():
    return '-' + ''.join(random.choices(string.ascii_uppercase +
                                        string.digits, k=5))


def parse_cooldown(cooldown):
    hours, remainder = divmod(int(cooldown), 3600)
    minutes, seconds = divmod(remainder, 60)

    return minutes, seconds


async def send_message(ctx=None, channel=None, content=None, embed=None, emoji=None):
    if emoji:
        try:
            await ctx.message.add_reaction(emoji)
        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    if ctx and not channel:
        channel = ctx

    else:
        pass

    if content and not embed:
        try:
            return await channel.send(content)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    elif embed and content:
        try:
            return await channel.send(content, embed=embed)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    elif not content and embed:
        try:
            return await channel.send(embed=embed)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass


async def reply_message(ctx, content=None, embed=None, emoji=None):
    if emoji:
        try:
            if isinstance(ctx, discord.Message):
                await ctx.add_reaction(emoji)

            else:
                await ctx.message.add_reaction(emoji)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    if content and not embed:
        try:
            return await ctx.reply(content, mention_author=False)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    elif embed and not content:
        try:
            return await ctx.reply(embed=embed, mention_author=False)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass


async def edit_message(msg, content=None, embed=None):
    if content and not embed:
        try:
            return await msg.edit(content)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    elif embed and not content:
        try:
            return await msg.edit(embed=embed)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass


async def reply_file(ctx, f, embed=None, emoji=None):
    if emoji:
        try:
            await ctx.message.add_reaction(emoji)
        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    if not embed:
        try:
            return await ctx.reply(file=f, mention_author=False)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass

    else:
        try:
            return await ctx.reply(embed=embed, file=f, mention_author=False)

        except (discord.Forbidden, discord.errors.Forbidden):
            pass


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
