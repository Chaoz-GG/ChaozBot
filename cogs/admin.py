import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.db import get_all_users
from utils.tools import log_message


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    sudo_role_ids = data['sudo_role_ids']
    chaoz_logo_url = data['chaoz_logo_url']

with open('data/games.json') as json_file:
    games = json.load(json_file)

    options = list()

    for index, game in enumerate(games.items()):
        options.append(app_commands.Choice(name=game[1][0], value=index))


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='view', description='View registered user list.')
    @app_commands.choices(region=[
        app_commands.Choice(name='North America', value=1),
        app_commands.Choice(name='South America', value=2),
        app_commands.Choice(name='Europe', value=3),
        app_commands.Choice(name='Africa', value=4),
        app_commands.Choice(name='Asia', value=5),
        app_commands.Choice(name='Oceania', value=6)
    ])
    @app_commands.choices(favorite_game=options)
    @app_commands.guilds(whitelist)
    async def _view(self, ctx: discord.Interaction,
                    region: app_commands.Choice[int] = None,
                    favorite_game: app_commands.Choice[int] = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content='This is an administrator only command.')

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_thumbnail(url=chaoz_logo_url)

        if region:
            region = region.name

        else:
            region = None

        if favorite_game:
            favorite_game = favorite_game.name

        else:
            favorite_game = None

        users = get_all_users(region=region, favorite_game=favorite_game)

        if not users:
            return await ctx.edit_original_message(content='No users found with the given constraints.')

        embed.title = 'Registered User List'
        embed.description = f'Total **{len(users)}** registered users\n\n'

        for user in enumerate(users):
            embed.description += f'`{user[0] + 1}.` {ctx.guild.get_member(user[1][0]).mention} - `{user[1][1]}`\n'

        await ctx.edit_original_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
