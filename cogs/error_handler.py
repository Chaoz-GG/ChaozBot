#!/usr/bin/python3

from discord.ext import commands
import discord

import json

from utils.tools import parse_cooldown, send_message, reply_message

from includes.errors import CustomError


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as f:
            data = json.load(f)

        self.log_channel_id = data['log_channel_id']
        self.prefix = data["prefix"]

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            message = f'Invalid syntax! Use `{self.prefix}help {ctx.command}` for details on usage of the command.'

        elif isinstance(error, commands.NoPrivateMessage):
            message = 'Sorry, this command cannot be executed in Direct Messages.'

        elif isinstance(error, commands.DisabledCommand):
            message = 'Sorry, this command is temporarily unavailable for usage.'

        elif isinstance(error, (discord.errors.Forbidden, discord.Forbidden)):
            message = 'Sorry, I\'m missing permissions to execute this command.'

        elif isinstance(error, CustomError):
            message = str(error)

        elif isinstance(error, commands.UserInputError):
            message = str(error)

        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.invoked_with == 'update':
                minutes, seconds = parse_cooldown(error.retry_after)

                message = 'Sorry, you can request a stats update once every 30 minutes. ' \
                          f'Come back in **{minutes}** minutes and **{seconds}** seconds.'

            else:
                message = f'You are on cooldown. Please try again in **{round(error.retry_after, 2)}** seconds.'

        else:
            embed = discord.Embed(colour=self.bot.embed_colour)

            embed.title = 'Unhandled Exception'
            embed.description = f'```css\n{str(error)}```\nAn unexpected error occurred during the execution ' \
                                f'of this command. It has been logged and reported to the developers.'

            await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji2)

            embed.description = ''

            embed.add_field(name='Command', value=f'`{ctx.command}`', inline=False)
            embed.add_field(name='Exception', value=f'```css\n{str(error)}```')

            channel = self.bot.get_channel(self.log_channel_id)

            return await send_message(channel=channel, embed=embed)

        await reply_message(ctx=ctx, content=message, emoji=self.bot.emoji2)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
