#!/usr/bin/python3

import discord
from discord.ext import commands

import math
from datetime import datetime

from utils.tools import reply_message, edit_message


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _ping(self, ctx):
        embed = discord.Embed(colour=self.bot.embed_colour)
        embed.description = '**Pong!**'

        ms = self.bot.latency*1000

        embed.add_field(name='API latency (Heartbeat)', value=f'`{int(ms)} ms`')

        t1 = datetime.utcnow().strftime("%f")

        msg = await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji1)

        t2 = datetime.utcnow().strftime("%f")

        diff = int(math.fabs((int(t2) - int(t1))/1000))

        embed.add_field(name='Bot latency (Round-trip)', value=f'`{diff} ms`')

        await edit_message(msg=msg, embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
