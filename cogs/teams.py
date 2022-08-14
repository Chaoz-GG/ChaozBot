import io
import json
import string
import random

import paramiko
from steam.webapi import WebAPI

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

from utils.tools import log_message
from utils.db import already_exists, get_steam_id, get_region, get_all_team_names, get_all_team_abbreviations, \
    create_team, update_team_message_id, update_team_active_game, update_team_region, update_team_description, \
    update_team_org_name, get_team_by_id, get_team_by_message_id, check_team_members_full, check_team_subsitutes_full, \
    add_team_member, add_team_substitute, check_team_member_exists, check_team_substitute_exists, get_team_members, \
    get_team_substitutes, remove_team_member, remove_team_substitute, remove_team, get_team_requested_members, \
    get_team_requested_substitutes, get_team_blacklist, add_team_requested_member, remove_team_requested_member, \
    add_team_requested_substitute, remove_team_requested_substitute, add_team_blacklist, remove_team_blacklist, \
    get_teams_by_captain_id


with open('config.json') as _json_file:
    _data = json.load(_json_file)
    whitelist = _data['whitelist']
    steam_key = _data['steam_key']
    create_team_channel_id = _data['create_team_channel_id']
    join_team_channel_id = _data['join_team_channel_id']
    sudo_role_ids = _data['sudo_role_ids']
    team_max_games = _data['team_max_games']

    chaoz_text = _data['chaoz_text']
    chaoz_logo_url = _data['chaoz_logo_url']

    sftp_host = _data['sftp_host']
    sftp_port = _data['sftp_port']
    sftp_username = _data['sftp_username']
    sftp_pvt_key = _data['sftp_pvt_key']
    sftp_pvt_key_password = _data['sftp_pvt_key_password']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["teams"]

steamAPI = WebAPI(steam_key)


class MemberRequest(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=43200)

        self.ctx = None
        self.team = None
        self.captain_discord_id = None
        self.member_steam_id = None
        self.member_discord_id = None
        self.member_text = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2714', style=discord.ButtonStyle.green, custom_id='persistent_view:accept_member')
    async def _accept(self, ctx: discord.Interaction, button: discord.ui.Button):
        add_team_member(self.team["id"], self.member_steam_id, self.member_discord_id)
        remove_team_requested_member(self.team["id"], self.member_discord_id)

        member = self.ctx.guild.get_member(self.member_discord_id)
        captain = self.ctx.guild.get_member(self.captain_discord_id)

        await log_message(ctx, f'`{member}` has been accepted into the team `{self.team["name"]}` as a member.')

        await member.send(messages["member_request_accept_member"].format(self.team["name"]))
        await ctx.response.send_message(messages["member_request_accept_captain"].format(self.member_text,
                                                                                         self.team["name"]),
                                        ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u274C', style=discord.ButtonStyle.red, custom_id='persistent_view:reject_member')
    async def _reject(self, ctx: discord.Interaction, button: discord.ui.Button):
        remove_team_requested_member(self.team["id"], self.member_discord_id)
        add_team_blacklist(self.team["id"], self.member_discord_id)

        member = self.ctx.guild.get_member(self.member_discord_id)
        captain = self.ctx.guild.get_member(self.captain_discord_id)

        await log_message(ctx, f'`{member}` has been rejected from the team `{self.team["name"]}` as a member.')

        await member.send(messages["member_request_reject_member"].format(self.team["name"]))
        await ctx.response.send_message(messages["member_request_reject_captain"].format(self.member_text,
                                                                                         self.team["name"]),
                                        ephemeral=True)

    async def on_timeout(self):
        remove_team_requested_member(self.team["id"], self.member_discord_id)

        captain = self.ctx.guild.get_member(self.captain_discord_id)
        await captain.send(messages["member_request_timeout_captain"].format(self.member_text, self.team["name"]))
        
    
class SubstituteRequest(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=43200)

        self.ctx = None
        self.team = None
        self.captain_discord_id = None
        self.substitute_steam_id = None
        self.substitute_discord_id = None
        self.substitute_text = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2714', style=discord.ButtonStyle.green, custom_id='persistent_view:accept_substitute')
    async def _accept(self, ctx: discord.Interaction, button: discord.ui.Button):
        add_team_substitute(self.team["id"], self.substitute_steam_id, self.substitute_discord_id)
        remove_team_requested_substitute(self.team["id"], self.substitute_discord_id)

        substitute = self.ctx.guild.get_member(self.substitute_discord_id)
        captain = self.ctx.guild.get_member(self.captain_discord_id)

        await log_message(ctx, f'`{substitute}` has been accepted into the team `{self.team["name"]}` as a substitute.')

        await substitute.send(messages["substitute_request_accept_substitute"].format(self.team["name"]))
        await ctx.response.send_message(messages["substitute_request_accept_captain"].format(self.substitute_text,
                                                                                             self.team["name"]),
                                        ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u274C', style=discord.ButtonStyle.red, custom_id='persistent_view:reject_substitute')
    async def _reject(self, ctx: discord.Interaction, button: discord.ui.Button):
        remove_team_requested_substitute(self.team["id"], self.substitute_discord_id)
        add_team_blacklist(self.team["id"], self.substitute_discord_id)

        substitute = self.ctx.guild.get_member(self.substitute_discord_id)
        captain = self.ctx.guild.get_member(self.captain_discord_id)

        await log_message(ctx, f'`{substitute}` has been rejected from the team `{self.team["name"]}` as a substitute.')

        await substitute.send(messages["substitute_request_reject_substitute"].format(self.team["name"]))
        await ctx.response.send_message(messages["substitute_request_reject_captain"].format(self.substitute_text,
                                                                                             self.team["name"]),
                                        ephemeral=True)

    async def on_timeout(self):
        remove_team_requested_substitute(self.team["id"], self.substitute_discord_id)

        captain = self.ctx.guild.get_member(self.captain_discord_id)
        await captain.send(messages["substitute_request_timeout_captain"].format(self.substitute_text,
                                                                                 self.team["name"]))


class Options(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.team = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Join as Member', style=discord.ButtonStyle.green, custom_id='persistent_view:join_member')
    async def _join_member(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not already_exists(ctx.user.id):
            return await ctx.response.send_message(messages["steam_account_link_warning"], ephemeral=True)

        team = self.team or get_team_by_message_id(ctx.message.id)

        steam_id = get_steam_id(ctx.user.id)

        if str(ctx.user.id) in get_team_requested_members(team["id"]) \
                or str(ctx.user.id) in get_team_requested_substitutes(team["id"]):
            return await ctx.response.send_message(messages["already_requested"], ephemeral=True)

        if str(ctx.user.id) in get_team_blacklist(team["id"]):
            return await ctx.response.send_message(messages["blacklisted"], ephemeral=True)

        if check_team_member_exists(team["id"], steam_id):
            return await ctx.response.send_message(messages["already_member"], ephemeral=True)

        if check_team_substitute_exists(team["id"], steam_id):
            return await ctx.response.send_message(messages["already_substitute"], ephemeral=True)

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in games.items():
            if _game[1][0] == team['active_game']:
                break

        # noinspection PyUnboundLocalVariable
        if check_team_members_full(team["id"], games[_game[0]][1]):
            return await ctx.response.send_message(messages["team_full"], ephemeral=True)

        # noinspection PyUnresolvedReferences
        steam_user = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        message = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) ' \
                  f'({ctx.user.mention}) would like to join your team **{team["name"]}** as a member.'

        view = MemberRequest()
        view.ctx = ctx
        view.team = team
        view.captain_discord_id = team["captain_discord_id"]
        view.member_steam_id = steam_id
        view.member_discord_id = ctx.user.id
        view.member_text = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) ' \
                           f'({ctx.user.mention})'

        captain = ctx.guild.get_member(team["captain_discord_id"])

        await captain.send(message, view=view)
        
        add_team_requested_member(team["id"], ctx.user.id)

        await log_message(ctx, f'`{ctx.user}` has requested to join the team `{team["name"]}` as a member.')

        await ctx.response.send_message(messages["request_placed"].format(team["name"]), ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Join as Substitute', style=discord.ButtonStyle.green,
                       custom_id='persistent_view:join_substitute')
    async def _join_substitute(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not already_exists(ctx.user.id):
            return await ctx.response.send_message(messages["steam_account_link_warning"], ephemeral=True)

        team = self.team or get_team_by_message_id(ctx.message.id)

        steam_id = get_steam_id(ctx.user.id)

        if str(ctx.user.id) in get_team_requested_members(team["id"]) \
                or str(ctx.user.id) in get_team_requested_substitutes(team["id"]):
            return await ctx.response.send_message(messages["already_requested"], ephemeral=True)

        if str(ctx.user.id) in get_team_blacklist(team["id"]):
            return await ctx.response.send_message(messages["blacklisted"], ephemeral=True)

        if check_team_substitute_exists(team["id"], steam_id):
            return await ctx.response.send_message(messages["already_substitute"], ephemeral=True)

        if check_team_member_exists(team["id"], steam_id):
            return await ctx.response.send_message(messages["already_member"], ephemeral=True)

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in games.items():
            if _game[1][0] == team['active_game']:
                break

        # noinspection PyUnboundLocalVariable
        if check_team_subsitutes_full(team["id"], games[_game[0]][1]):
            return await ctx.response.send_message(messages["team_full"], ephemeral=True)

        # noinspection PyUnresolvedReferences
        steam_user = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        message = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) ' \
                  f'({ctx.user.mention}) would like to join your team **{team["name"]}** as a substitute.'

        view = SubstituteRequest()
        view.ctx = ctx
        view.team = team
        view.captain_discord_id = team["captain_discord_id"]
        view.substitute_steam_id = steam_id
        view.substitute_discord_id = ctx.user.id
        view.substitute_text = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) ' \
                               f'({ctx.user.mention})'

        captain = ctx.guild.get_member(team["captain_discord_id"])

        await captain.send(message, view=view)
        
        add_team_requested_substitute(team["id"], ctx.user.id)

        await log_message(ctx, f'`{ctx.user}` has requested to join the team `{team["name"]}` as a substitute.')

        await ctx.response.send_message(messages["request_placed"].format(team["name"]), ephemeral=True)


class Team(ui.Modal, title='New Chaoz Team'):
    options = list()

    with open('data/games.json') as f:
        games = json.load(f)

    for abbr, game in games.items():
        options.append(discord.SelectOption(label=game[0], value=abbr))

    game = ui.Select(placeholder='Choose your game(s) ...', options=options, max_values=team_max_games)
    name = ui.TextInput(label='Name', placeholder='The team name', max_length=50)
    description = ui.TextInput(label='Description',
                               placeholder='The team description',
                               style=discord.TextStyle.long,
                               max_length=300,
                               required=False)
    org_name = ui.TextInput(label='Organization Name',
                            placeholder='Name of the organization this team belongs to',
                            max_length=50,
                            required=False)
    abbreviation = ui.TextInput(label='Abbreviation', placeholder='5-letter abbreviation for your team', max_length=5)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True, ephemeral=True)

        if self.name.value in get_all_team_names():
            return await ctx.edit_original_message(content=messages["team_name_exists"])

        if self.abbreviation.value.upper() in get_all_team_abbreviations():
            return await ctx.edit_original_message(content=messages["team_abbreviation_exists"])

        team_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        steam_id = get_steam_id(ctx.user.id)
        region = get_region(ctx.user.id)

        _games = list()

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in self.game.values:
            _games.append(games[_game][0])

        create_team(team_id, "|".join(_games), games[self.game.values[0]][0], self.name.value,
                    self.abbreviation.value.upper(), region, steam_id, ctx.user.id,
                    org_name=self.org_name.value, description=self.description.value)

        key = paramiko.RSAKey.from_private_key_file(sftp_pvt_key, password=sftp_pvt_key_password)

        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)

        with open('assets/images/team-default.png') as f:
            sftp.putfo(f, f'public_html/teams/{team_id}.png')

        sftp.close()
        transport.close()

        join_team_channel = ctx.guild.get_channel(join_team_channel_id)

        embed = discord.Embed(colour=0xffffff)

        embed.title = self.name.value
        embed.description = self.description.value

        embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)

        embed.set_thumbnail(url=f'https://bot.chaoz.gg/teams/{team_id}.png')

        embed.add_field(name='Team ID', value=f'`{team_id}`')
        embed.add_field(name='Game(s)', value=', '.join(_games))
        embed.add_field(name='Active Game', value=f'**{games[self.game.values[0]][0]}**')
        embed.add_field(name='Abbreviation', value=f'`{self.abbreviation.value.upper()}`')

        if self.org_name.value:
            embed.add_field(name='Organization', value=f'**{self.org_name.value}**')

        embed.add_field(name='Region', value=region)
        embed.add_field(name='Captain', value=ctx.user.mention)

        embed.set_footer(text=games[self.game.values[0]][0],
                         icon_url=f'https://bot.chaoz.gg/assets/{self.game.values[0]}.png')

        view = Options()

        msg = await join_team_channel.send(embed=embed, view=view)

        update_team_message_id(team_id, msg.id)
        add_team_member(team_id, steam_id, ctx.user.id)

        await log_message(ctx, f'`{ctx.user}` has created a new team `{self.name.value}`.')

        return await ctx.edit_original_message(content=messages["team_created"].format(self.name.value))


class Edit(ui.Modal, title='Edit Team'):
    def __init__(self):
        super().__init__()

        self.ctx = None
        self.team_id = None

    active_game = ui.Select(placeholder='Choose your active game ...', min_values=0, max_values=1)
    region = ui.Select(placeholder='Choose your region ...', min_values=0, max_values=1)
    description = ui.TextInput(label='Description',
                               placeholder='The team description',
                               style=discord.TextStyle.long,
                               max_length=300,
                               required=False)
    org_name = ui.TextInput(label='Organization Name',
                            placeholder='Name of the organization this team belongs to',
                            max_length=50,
                            required=False)

    async def on_submit(self, ctx: discord.Interaction):
        await ctx.response.defer()

        team = get_team_by_id(self.team_id)

        channel = ctx.guild.get_channel(join_team_channel_id)
        message = await channel.fetch_message(team["message_id"])
        embed = message.embeds[0]

        with open('data/games.json') as f:
            games = json.load(f)

        if self.active_game.values:
            update_team_active_game(self.team_id, games[self.active_game.values[0]][0])
            embed.set_field_at(2, name='Active Game', value=f'**{games[self.active_game.values[0]][0]}**')
            embed.set_footer(text=games[self.active_game.values[0]][0],
                             icon_url=f'https://bot.chaoz.gg/games/{self.active_game.values[0]}.png')

        if self.region.values:
            update_team_region(self.team_id, self.region.values[0])
            embed.set_field_at(5, name='Region', value=self.region.values[0])

        if self.description.value:
            update_team_description(self.team_id, self.description.value)
            embed.description = self.description.value

        if self.org_name.value:
            update_team_org_name(self.team_id, self.org_name.value)
            embed.set_field_at(4, name='Organization', value=f'**{self.org_name.value}**')

        await message.edit(embed=embed)

        await log_message(ctx, f'`{self.ctx.user}` has edited team `{team["name"]}`.')
        
        return await self.ctx.edit_original_message(content=messages["team_updated"].format(team["name"]),
                                                    embed=None, view=None)


class MemberSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None
        self.team_id = None

        super().__init__(placeholder='Choose the member to remove.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        remove_team_member(self.team_id, self.values[0])

        await log_message(ctx, f'`{self.ctx.user}` has removed member `{self.values[0]}` '
                               f'from team `{get_team_by_id(self.team_id)["name"]}`.')

        await self.ctx.edit_original_message(content=messages["action_success"], embed=None, view=None)


class SubstituteSelect(discord.ui.Select):
    def __init__(self, options):

        self.ctx = None
        self.team_id = None

        super().__init__(placeholder='Choose the substitute to remove.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        remove_team_substitute(self.team_id, self.values[0])

        await log_message(ctx, f'`{self.ctx.user}` has removed substitute `{self.values[0]}` '
                               f'from team `{get_team_by_id(self.team_id)["name"]}`.')

        await self.ctx.edit_original_message(content=messages["action_success"], embed=None, view=None)


class BlacklistSelect(discord.ui.Select):
    def __init__(self, options):

        self.ctx = None
        self.team_id = None

        super().__init__(placeholder='Choose the blacklisted user to remove.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        remove_team_blacklist(self.team_id, self.values[0])

        await log_message(ctx, f'`{self.ctx.user}` has removed blacklisted user `{self.values[0]}` '
                               f'from team `{get_team_by_id(self.team_id)["name"]}`.')

        await self.ctx.edit_original_message(content=messages["action_success"], embed=None, view=None)


class TeamCPSelect(discord.ui.Select):
    def __init__(self, options):

        self.ctx = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        view = CP()
        view.ctx = ctx
        view.team_id = self.values[0]

        await ctx.edit_original_message(content=messages["action_select"], embed=None, view=view)


class TeamLogoSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None
        self.logo = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        await self.ctx.edit_original_message(content='Updating logo ...', embed=None, view=None)

        key = paramiko.RSAKey.from_private_key_file(sftp_pvt_key, password=sftp_pvt_key_password)

        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.putfo(self.logo, f'public_html/teams/{self.values[0]}.png')

        sftp.close()
        transport.close()

        team = get_team_by_id(self.values[0])

        channel = ctx.guild.get_channel(join_team_channel_id)
        message = await channel.fetch_message(team['message_id'])
        embed = message.embeds[0]
        embed.set_thumbnail(url=f'https://bot.chaoz.gg/teams/{self.values[0]}.png')
        await message.edit(embed=embed)

        await log_message(self.ctx, f'`{self.ctx.user}` has updated the logo for `{team["name"]}`.')

        await self.ctx.edit_original_message(content=messages["logo_updated"], embed=None, view=None)


class TeamEmbedPublish(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=options.__len__(), options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        await self.ctx.edit_original_message(content=messages["embeds_publishing"], embed=None, view=None)

        for team_id in self.values:
            team = get_team_by_id(team_id)

            embed = discord.Embed(colour=0xffffff)

            embed.title = team['name']
            embed.description = team['description']

            embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)

            embed.set_thumbnail(url=f'https://bot.chaoz.gg/teams/{team_id}.png')

            embed.add_field(name='Team ID', value=f'`{team["id"]}`')
            embed.add_field(name='Game(s)', value=', '.join(team["games"].split("|")))
            embed.add_field(name='Active Game', value=f'**{team["active_game"]}**')
            embed.add_field(name='Abbreviation', value=f'`{team["abbreviation"].upper()}`')

            if team['org_name']:
                embed.add_field(name='Organization', value=f'**{team["org_name"]}**')

            embed.add_field(name='Region', value=team['region'])

            captain = ctx.guild.get_member(team['captain_discord_id'])

            embed.add_field(name='Captain', value=captain.mention)

            with open('data/games.json') as f:
                games = json.load(f)

            for _game in games.items():
                if _game[1][0] == team['active_game']:
                    embed.set_footer(text=team['active_game'], icon_url=f'https://bot.chaoz.gg/games/{_game[0]}.png')

            view = Options()
            view.team = team

            join_team_channel = ctx.guild.get_channel(join_team_channel_id)

            msg = await join_team_channel.send(embed=embed, view=view)
            update_team_message_id(team_id, msg.id)

            await log_message(self.ctx, f'`{self.ctx.user}` has published the embed for `{team["name"]}`.')

        await self.ctx.edit_original_message(content=messages["embeds_published"], embed=None, view=None)


class DeleteConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.ctx = None
        self.team_id = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2714',
                       style=discord.ButtonStyle.green,
                       custom_id='persistent_view:delete_confirm')
    async def _confirm(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        team = get_team_by_id(self.team_id)

        join_team_channel = ctx.guild.get_channel(join_team_channel_id)

        try:
            message = await join_team_channel.fetch_message(team['message_id'])
            await message.delete()

        except (discord.NotFound, discord.HTTPException):
            pass

        key = paramiko.RSAKey.from_private_key_file(sftp_pvt_key, password=sftp_pvt_key_password)

        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            sftp.remove(f'public_html/teams/{self.team_id}.png')

        except FileNotFoundError:
            pass

        sftp.close()
        transport.close()

        await log_message(self.ctx, f'`{self.ctx.user}` has deleted the team `{team["name"]}`.')

        remove_team(self.team_id)

        await self.ctx.edit_original_message(content=messages["action_success"], view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u274C',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:delete_cancel')
    async def _cancel(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        await self.ctx.edit_original_message(content=messages["action_cancel"], view=None)


class CP(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.ctx = None
        self.team_id = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Edit Team Details',
                       style=discord.ButtonStyle.green,
                       custom_id='persistent_view:edit_team_details')
    async def _edit_team(self, ctx: discord.Interaction, button: discord.ui.Button):
        team = get_team_by_id(self.team_id)

        active_game_options = list()

        regions = [
            "North America",
            "South America",
            "Europe",
            "Africa",
            "Asia",
            "Oceania"
        ]
        region_options = list()

        with open('data/games.json') as f:
            games = json.load(f)

        for game in team['games'].split('|'):
            for _game in games.items():
                if _game[1][0] == game:
                    if _game[1][0] == team['active_game']:
                        active_game_options.append(discord.SelectOption(value=_game[0], label=_game[1][0],
                                                                        default=True))

                    else:
                        active_game_options.append(discord.SelectOption(value=_game[0], label=_game[1][0]))

        for _region in regions:
            if _region == team['region']:
                region_options.append(discord.SelectOption(value=_region, label=_region, default=True))

            else:
                region_options.append(discord.SelectOption(value=_region, label=_region))

        modal = Edit()
        modal.ctx = ctx
        modal.team_id = self.team_id
        modal.active_game.options = active_game_options
        modal.region.options = region_options
        await ctx.response.send_modal(modal)
        await modal.wait()

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Manage Members',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:manage_members')
    async def _manage_members(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Manage Members'
        embed.description = 'Which member would you like to remove?\n'

        member_data = get_team_members(self.team_id)
        captain = str(get_team_by_id(self.team_id)['captain_steam_id'])
        member_data.pop(captain)

        if not member_data:
            await self.ctx.edit_original_message(content=messages["no_member_data"], view=None)

        i = 1
        options = list()

        for steam_id, discord_id in member_data.items():
            # noinspection PyUnresolvedReferences
            steam_user = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=int(steam_id))["response"]["players"][0]
            discord_user = self.ctx.guild.get_member(int(discord_id))

            embed.description += f'\n`{i}.` [{steam_user["personaname"]}](https://steamcommunity.com/profiles/' \
                                 f'{steam_id}) - {discord_user.mention})'

            options.append(discord.SelectOption(label=str(i), value=str(steam_id)))

            i += 1

        item = MemberSelect(options)
        item.ctx = ctx
        item.team_id = self.team_id

        view = discord.ui.View()
        view.add_item(item)

        await self.ctx.edit_original_message(embed=embed, view=view)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Manage Substitutes',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:manage_substitutes')
    async def _manage_substitutes(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Manage Substitutes'
        embed.description = 'Which substitute would you like to remove?\n'

        substitute_data = get_team_substitutes(self.team_id)

        if not substitute_data:
            await self.ctx.edit_original_message(content=messages["no_substitute_data"], view=None)

        i = 1
        options = list()

        for steam_id, discord_id in substitute_data.items():
            # noinspection PyUnresolvedReferences
            steam_user = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=int(steam_id))["response"]["players"][0]
            discord_user = self.ctx.guild.get_member(int(discord_id))

            embed.description += f'\n`{i}.` [{steam_user["personaname"]}](https://steamcommunity.com/profiles/' \
                                 f'{steam_id}) - {discord_user.mention})'

            options.append(discord.SelectOption(label=str(i), value=str(steam_id)))

            i += 1

        item = SubstituteSelect(options)
        item.ctx = ctx
        item.team_id = self.team_id

        view = discord.ui.View()
        view.add_item(item)

        await self.ctx.edit_original_message(embed=embed, view=view)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Manage Blacklist',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:manage_blacklist')
    async def _manage_blacklist(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Manage Blacklist'
        embed.description = 'Which blacklisted user would you like to remove?\n'

        blacklist_data = get_team_blacklist(self.team_id)

        if not blacklist_data:
            await self.ctx.edit_original_message(content=messages["no_blacklist_data"], view=None)

        i = 1
        options = list()

        for discord_id in blacklist_data:
            discord_user = self.ctx.guild.get_member(int(discord_id))

            embed.description += f'\n`{i}.` {discord_user.mention})'

            options.append(discord.SelectOption(label=str(i), value=str(discord_id)))

            i += 1

        item = BlacklistSelect(options)
        item.ctx = ctx
        item.team_id = self.team_id

        view = discord.ui.View()
        view.add_item(item)

        await self.ctx.edit_original_message(embed=embed, view=view)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Delete Team',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:delete_team')
    async def _delete_team(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        view = DeleteConfirm()

        view.ctx = self.ctx
        view.team_id = self.team_id

        await self.ctx.edit_original_message(content=messages["delete_confirm"], view=view)


class Create(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2795', style=discord.ButtonStyle.green, custom_id='persistent_view:create')
    async def _create(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not already_exists(ctx.user.id):
            return await ctx.response.send_message(messages["steam_account_link_warning"], ephemeral=True)

        modal = Team()
        await ctx.response.send_modal(modal)
        await modal.wait()


class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.steamAPI = steamAPI

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.create_team_channel_id = data['create_team_channel_id']
            self.join_team_channel_id = data['join_team_channel_id']

    async def _send_initial_message(self):
        create_team_channel = self.bot.get_channel(self.create_team_channel_id)

        with open('data/teams.json') as f:
            try:
                data = json.load(f)

                if 'message_id' in data.keys():
                    try:
                        return await create_team_channel.fetch_message(data["message_id"])

                    except discord.errors.NotFound:
                        pass

            except json.decoder.JSONDecodeError:
                pass

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Team Creator'
        embed.description = f"""
This tool helps you in creating a team.

- You need to have your **Steam account linked with the bot** (so does everyone joining the team).
- Once you create a team, **you become it's captain.**
- Members joining the team **require the captain's approval.**
- Captains are in-charge of managing a team's participation into events.
- You may select multiple games while creating a team, however, you can have only **one active game** at a time. 
  The game you select first becomes your team's active game, which you can change later from the control panel.  

To create a new team, press the \u2795 button.
"""

        embed.set_thumbnail(url=chaoz_logo_url)

        view = Create()

        msg = await create_team_channel.send(embed=embed, view=view)
        await msg.pin()

        with open('data/teams.json', 'w') as f:
            json.dump({
                'message_id': msg.id
            }, f)

        await view.wait()

    @commands.Cog.listener()
    async def on_ready(self):
        await self._send_initial_message()

    @app_commands.command(name='teamcp', description='Team Control Panel.')
    @app_commands.guilds(whitelist)
    async def _team_cp(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                teams = get_teams_by_captain_id(-1)
                break

        else:
            teams = get_teams_by_captain_id(ctx.user.id)

        if not teams:
            return await ctx.edit_original_message(content=messages["no_captain"])

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Select Team'
        embed.description = 'Which team would you like to launch the control panel for?\n'

        options = list()

        for i, team_details in enumerate(teams, 1):
            embed.description += f'\n`{i}.` {team_details[1]}'

            options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

        item = TeamCPSelect(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='teamlogo', description='Upload team logo.')
    @app_commands.guilds(whitelist)
    async def _team_logo(self, ctx: discord.Interaction, logo: discord.Attachment):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                teams = get_teams_by_captain_id(-1)
                break

        else:
            teams = get_teams_by_captain_id(ctx.user.id)

        if not teams:
            return await ctx.edit_original_message(content=messages["no_captain"])

        _logo = io.BytesIO(await logo.read())

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Select Team'
        embed.description = 'Which team would you like to update the logo for?\n'

        options = list()

        for i, team_details in enumerate(teams, 1):
            embed.description += f'\n`{i}.` {team_details[1]}'

            options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

        item = TeamLogoSelect(options=options)
        item.ctx = ctx
        item.logo = _logo

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='teaminfo', description='Team Information.')
    @app_commands.guilds(whitelist)
    async def _team_info(self, ctx: discord.Interaction, team_id: str):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        team_id = team_id.upper()
        team = get_team_by_id(team_id)

        if not team:
            return await ctx.edit_original_message(content=messages["team_not_found"])

        embed = discord.Embed(colour=0xffffff)

        embed.title = team['name']
        embed.description = team['description']

        embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)

        embed.set_thumbnail(url=f'https://bot.chaoz.gg/teams/{team_id}.png')

        embed.add_field(name='Team ID', value=f'`{team["id"]}`')
        embed.add_field(name='Game(s)', value=', '.join(team["games"].split("|")))
        embed.add_field(name='Active Game', value=f'**{team["active_game"]}**')
        embed.add_field(name='Abbreviation', value=f'`{team["abbreviation"].upper()}`')

        if team['org_name']:
            embed.add_field(name='Organization', value=f'**{team["org_name"]}**')

        embed.add_field(name='Region', value=team['region'])

        captain = ctx.guild.get_member(team['captain_discord_id'])

        embed.add_field(name='Captain', value=captain.mention)

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in games.items():
            if _game[1][0] == team['active_game']:
                embed.set_footer(text=team['active_game'], icon_url=f'https://bot.chaoz.gg/games/{_game[0]}.png')

        view = Options()
        view.team = team

        await ctx.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='publish_teams', description='Publish the embed for team(s).')
    @app_commands.guilds(whitelist)
    async def _publish_lb(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

        teams = get_teams_by_captain_id(-1)

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Select Team'
        embed.description = 'Which team would you like to update the logo for?\n'

        options = list()

        for i, team_details in enumerate(teams, 1):
            embed.description += f'\n`{i}.` {team_details[1]}'

            options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

        item = TeamEmbedPublish(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Teams(bot))
