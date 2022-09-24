import io
import json

import paramiko

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

from utils.db import get_team_by_id, update_team_active_game, get_all_teams_and_games, update_team_games
from utils.tools import log_message

with open('config.json') as _json_file:
    _data = json.load(_json_file)
    whitelist = _data['whitelist']
    join_team_channel_id = _data['join_team_channel_id']
    sudo_role_ids = _data['sudo_role_ids']
    chaoz_logo_url = _data['chaoz_logo_url']

    sftp_host = _data['sftp_host']
    sftp_port = _data['sftp_port']
    sftp_username = _data['sftp_username']
    sftp_pvt_key = _data['sftp_pvt_key']
    sftp_pvt_key_password = _data['sftp_pvt_key_password']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["games"]


# Form for adding a game to the list of available games
class Add(ui.Modal, title='Add Game'):
    abbreviation = ui.TextInput(label='Abbreviation', placeholder='Abbreviation for the game', max_length=10)
    name = ui.TextInput(label='Name', placeholder='The name of the game', max_length=50)
    max_players = ui.TextInput(label='Maximum Players', placeholder='The max number of players / subs')
    description = ui.TextInput(label='Description',
                               placeholder='The game\'s short description',
                               style=discord.TextStyle.long,
                               max_length=1000,
                               required=False)
    url = ui.TextInput(label='URL', placeholder='Link to the game article on the website.')

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True, ephemeral=True)

        with open('data/games.json') as f:
            games = json.load(f)

        # Create a game object with the given values
        games[self.abbreviation.value.lower()] = [
            self.name.value,
            int(self.max_players.value),
            self.description.value or "",
            self.url.value]

        # Dump the updated games list to the file
        with open('data/games.json', 'w') as f:
            json.dump(games, f, indent=4)

        await log_message(ctx, f'The game `{self.name.value}` has been added by `{ctx.user}`.')

        return await ctx.edit_original_response(content=messages["add_game_success"])


# Form for editing an existing game
class Edit(ui.Modal, title='Edit Team'):
    def __init__(self):
        super().__init__()

        self.ctx = None
        self.game_id = None

    max_players = ui.TextInput(label='Maximum Players', placeholder='The max number of players / subs', required=False)
    description = ui.TextInput(label='Description',
                               placeholder='The game\'s short description',
                               style=discord.TextStyle.long,
                               max_length=1000,
                               required=False)
    url = ui.TextInput(label='URL', placeholder='Link to the game article on the website.', required=False)

    async def on_submit(self, ctx: discord.Interaction):
        await ctx.response.defer()

        with open('data/games.json') as f:
            games = json.load(f)

        game = games[self.game_id]

        if self.max_players.value:
            game[1] = int(self.max_players.value)

        if self.description.value:
            game[2] = self.description.value

        if self.url.value:
            game[3] = self.url.value

        # Dump the updated games list to the file
        with open('data/games.json', 'w') as f:
            json.dump(games, f, indent=4)

        await log_message(self.ctx, f'Game `{game[0]}` has been updated by `{self.ctx.user}`.')

        return await self.ctx.edit_original_response(content=messages["game_updated"], embed=None, view=None)


class GameInfoSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the game.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        with open('data/games.json') as f:
            games = json.load(f)

        _game = games[self.values[0]]

        embed = discord.Embed(colour=0xffffff)

        embed.title = _game[0]
        embed.description = _game[2]

        embed.set_thumbnail(url=f'https://bot.chaoz.gg/games/{self.values[0]}.png')

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Read More', url=_game[3]))

        await self.ctx.edit_original_response(embed=embed, view=view)


class RemoveGameSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the game.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        await self.ctx.edit_original_response(content='Processing ...', embed=None, view=None)

        # Load existing game data
        with open('data/games.json') as f:
            __games = json.load(f)

        _game = self.values[0]
        game_name = __games[_game][0]

        # While removing a game we need to ensure that we remove it from the list of games a team has set, if it exists
        # and also remove it as the active game if it is set as the active game for a team
        for team_id, games, active_game in get_all_teams_and_games():
            team = get_team_by_id(team_id)
            channel = ctx.guild.get_channel(join_team_channel_id)
            message = await channel.fetch_message(team['message_id'])
            embed = message.embeds[0]

            games = games.split('|')

            if game_name in games:
                games.pop(games.index(game_name))

                if not games:
                    games.append('Other Game')

                _games = ', '.join(games)
                games = '|'.join(games)

                update_team_games(team_id, games)
                embed.set_field_at(1, name='Game(s)', value=_games)

            if active_game == game_name:
                update_team_active_game(team_id, 'Other Game')
                embed.set_field_at(2, name='Active Game', value='Other Game')

            embed.set_footer(text='Other Game', icon_url=f'https://bot.chaoz.gg/games/other.png')

            await message.edit(embed=embed)

        # Remove the game from the games list
        __games.pop(_game)

        # Dump the updated games list to the file
        with open('data/games.json', 'w') as f:
            json.dump(__games, f, indent=4)

        await log_message(self.ctx, f'The game `{game_name}` has been removed by `{self.ctx.user}`.')

        return await self.ctx.edit_original_response(content=messages["game_removed"], embed=None, view=None)


class GameLogoSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None
        self.logo = None

        super().__init__(placeholder='Select the game.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        await self.ctx.edit_original_response(content='Updating logo ...', embed=None, view=None)

        # Create SFTP connection to our server
        key = paramiko.RSAKey.from_private_key_file(sftp_pvt_key, password=sftp_pvt_key_password)

        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Copy the uploaded logo to the relevant location on the server
        sftp.putfo(self.logo, f'public_html/games/{self.values[0]}.png')

        sftp.close()
        transport.close()

        await log_message(self.ctx, f'The logo for `{self.values[0]}` has been updated by `{self.ctx.user}`.')

        await self.ctx.edit_original_response(content=messages["game_logo_updated"], embed=None, view=None)


class GameEditSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the game.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        modal = Edit()
        modal.ctx = ctx
        modal.game_id = self.values[0]
        await ctx.response.send_modal(modal)
        await modal.wait()


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='gameinfo', description='Show information about a supported game.')
    @app_commands.guilds(whitelist)
    async def _game_info(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        embed = discord.Embed(colour=0xffffff)

        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

        embed.title = 'Select Game'
        embed.description = 'Which game would you like to look up?\n'

        with open('data/games.json') as f:
            games = json.load(f)

        # Create existing game data select options
        options = list()

        for i, game_details in enumerate(games.items(), 1):
            embed.description += f'\n`{i}.` {game_details[1][0]}'

            options.append(discord.SelectOption(label=game_details[1][0], value=game_details[0]))

        item = GameInfoSelect(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name='gamelogo', description='Upload game logo.')
    @app_commands.guilds(whitelist)
    async def _game_logo(self, ctx: discord.Interaction, logo: discord.Attachment):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Bypass for sudo (administrative) roles
        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_response(content=messages["admin_only"])

        # Read the logo bytes from the uploaded image file
        _logo = io.BytesIO(await logo.read())

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

        embed.title = 'Select Game'
        embed.description = 'Which game would you like to update the logo for?\n'

        with open('data/games.json') as f:
            games = json.load(f)

        # Create the game select options list
        options = list()

        for i, game_details in enumerate(games.items(), 1):
            embed.description += f'\n`{i}.` {game_details[1][0]}'

            options.append(discord.SelectOption(label=game_details[1][0], value=game_details[0]))

        item = GameLogoSelect(options=options)
        item.ctx = ctx
        item.logo = _logo

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name='addgame', description='Add a game to the games list. Admin only!')
    @app_commands.guilds(whitelist)
    async def _add_game(self, ctx: discord.Interaction):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Bypass for sudo (administrative) roles
        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_response(content=messages["admin_only"])

        modal = Add()
        await ctx.response.send_modal(modal)
        await modal.wait()

    @app_commands.command(name='editgame', description='Edit a game\'s details.')
    @app_commands.guilds(whitelist)
    async def _edit_game(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Bypass for sudo (administrative) roles
        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_response(content=messages["admin_only"])

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

        embed.title = 'Select Game'
        embed.description = 'Which game would you like to update the logo for?\n'

        with open('data/games.json') as f:
            games = json.load(f)

        # Create the game select options list
        options = list()

        for i, game_details in enumerate(games.items(), 1):
            embed.description += f'\n`{i}.` {game_details[1][0]}'

            options.append(discord.SelectOption(label=game_details[1][0], value=game_details[0]))

        item = GameEditSelect(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name='removegame', description='Remove a game from games list. Admin only!')
    @app_commands.guilds(whitelist)
    async def _remove_game(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Bypass for sudo (administrative) roles
        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_response(content=messages["admin_only"])

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

        embed.title = 'Select Game'
        embed.description = 'Which game would you like to update the logo for?\n'

        with open('data/games.json') as f:
            games = json.load(f)

        # Create the game select options list
        options = list()

        for i, game_details in enumerate(games.items(), 1):
            embed.description += f'\n`{i}.` {game_details[1][0]}'

            options.append(discord.SelectOption(label=game_details[1][0], value=game_details[0]))

        item = RemoveGameSelect(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_response(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Games(bot))
