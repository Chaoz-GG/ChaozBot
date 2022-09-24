import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.tools import log_message


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']

    chaoz_logo_url = data['chaoz_logo_url']


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Help command!')
    @app_commands.choices(user_type=[
        app_commands.Choice(name='Regular', value='regular'),
        app_commands.Choice(name='Admin', value='admin'),
    ])
    @app_commands.guilds(whitelist)
    async def _help(self, ctx: discord.Interaction, user_type: app_commands.Choice[str]):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if user_type:
            user_type = user_type.value

        else:
            user_type = 'regular'

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_thumbnail(url=chaoz_logo_url)

        # NOTE: For each new command, wrap the command name in `` and place it in the relevant section of the embed

        if user_type == 'regular':
            embed.title = 'Regular Commands'

            embed.add_field(name='General',
                            value=f'`ping`',
                            inline=False)

            embed.add_field(name='Profile',
                            value=f'`profile`, `link`, `unlink`, `setup`, `country`, `inv`',
                            inline=False)

            embed.add_field(name='Statistics',
                            value=f'`mmstats`, `faceitstats`, `update`',
                            inline=False)

            embed.add_field(name='Games',
                            value=f'`gameinfo`',
                            inline=False)

            embed.add_field(name='Teams',
                            value=f'`teaminfo`, `teamcp`, `teamlogo`',
                            inline=False)

        else:
            embed.title = 'Admin Commands'

            embed.add_field(name='General',
                            value=f'`view`',
                            inline=False)

            embed.add_field(name='Profile',
                            value=f'`forcelink`, `forceunlink`, `forceadd`, `prune_users`',
                            inline=False)

            embed.add_field(name='Leaderboard',
                            value=f'`publish_lb`',
                            inline=False)

            embed.add_field(name='Teams',
                            value=f'`forceadd`, `publish_teams`',
                            inline=False)

            embed.add_field(name='Games',
                            value=f'`addgame`, `editgame`, `removegame`, `gamelogo`',
                            inline=False)

        await ctx.edit_original_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
