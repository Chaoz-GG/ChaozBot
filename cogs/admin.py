import json
from contextlib import suppress

import discord
from discord import app_commands
from discord.ext import commands

import aiohttp
import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID

from utils.db import get_all_users, get_steam_id, get_steam_ids, already_exists, add_user, remove_user, update_hours, \
    update_country, update_region, get_team_by_id, get_teams_by_captain_id, check_team_member_exists, \
    check_team_substitute_exists, check_team_members_full, check_team_subsitutes_full, add_team_member, \
    add_team_substitute, remove_team_requested_member, remove_team_requested_substitute, remove_team_blacklist
from utils.tools import log_message


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    steam_key = data['steam_key']
    sudo_role_ids = data['sudo_role_ids']
    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']
    chaoz_logo_url = data['chaoz_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["admin"]

with open('data/games.json') as json_file:
    games = json.load(json_file)

    options = list()

    for index, game in enumerate(games.items()):
        options.append(app_commands.Choice(name=game[1][0], value=index))


class UnlinkConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.ctx = None
        self.member = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2714',
                       style=discord.ButtonStyle.green,
                       custom_id='persistent_view:unlink_confirm')
    async def _confirm(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        steam_id = get_steam_id(self.member.id)

        remove_user(self.member.id, steam_id)

        return await self.ctx.edit_original_message(content=messages["profile_unlink_success"].format(self.member),
                                                    view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u274C',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:unlink_cancel')
    async def _cancel(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        await self.ctx.edit_original_message(content=messages["action_cancel"], view=None)


class TeamMemberForceAdd(discord.ui.Select):
    # noinspection PyShadowingNames
    def __init__(self, options):

        self.ctx = None
        self.member = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        team = get_team_by_id(self.values[0])
        steam_id = get_steam_id(self.member.id)

        if check_team_member_exists(team["id"], steam_id):
            return await self.ctx.edit_original_message(content=messages["already_member"], embed=None, view=None)

        if check_team_substitute_exists(team["id"], steam_id):
            return await self.ctx.edit_original_message(content=messages["already_substitute"], embed=None, view=None)

        with open('data/games.json') as f:
            _games = json.load(f)

        for _game in _games.items():
            if _game[1][0] == team['active_game']:
                break

        # noinspection PyUnboundLocalVariable
        if check_team_members_full(team["id"], _games[_game[0]][1]):
            return await self.ctx.edit_original_message(content=messages["team_full"], embed=None, view=None)

        add_team_member(team["id"], steam_id, self.member.id)

        with suppress(ValueError):
            remove_team_requested_member(team["id"], self.member.id)
            remove_team_requested_substitute(team["id"], self.member.id)
            remove_team_blacklist(team["id"], self.member.id)

        await log_message(ctx, messages["team_member_force_add"].format(ctx.user, self.member, team["name"]))

        await self.ctx.edit_original_message(content=messages["action_success"], embed=None, view=None)


class TeamSubstituteForceAdd(discord.ui.Select):
    # noinspection PyShadowingNames
    def __init__(self, options):

        self.ctx = None
        self.substitute = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        await ctx.response.defer()

        team = get_team_by_id(self.values[0])
        steam_id = get_steam_id(self.substitute.id)

        if check_team_member_exists(team["id"], steam_id):
            return await self.ctx.edit_original_message(content=messages["already_member"], embed=None, view=None)

        if check_team_substitute_exists(team["id"], steam_id):
            return await self.ctx.edit_original_message(content=messages["already_substitute"], embed=None, view=None)

        with open('data/games.json') as f:
            _games = json.load(f)

        for _game in _games.items():
            if _game[1][0] == team['active_game']:
                break

        # noinspection PyUnboundLocalVariable
        if check_team_subsitutes_full(team["id"], _games[_game[0]][1]):
            return await self.ctx.edit_original_message(content=messages["team_full"], embed=None, view=None)

        add_team_substitute(team["id"], steam_id, self.substitute.id)

        with suppress(ValueError):
            remove_team_requested_member(team["id"], self.substitute.id)
            remove_team_requested_substitute(team["id"], self.substitute.id)
            remove_team_blacklist(team["id"], self.substitute.id)

        await log_message(ctx, messages["team_substitute_force_add"].format(ctx.user, self.substitute, team["name"]))

        await self.ctx.edit_original_message(content=messages["action_success"], embed=None, view=None)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.steamAPI = WebAPI(steam_key)

        self.mm_rank_role_ids = mm_rank_role_ids
        self.faceit_rank_role_ids = faceit_rank_role_ids
        self.region_role_ids = region_role_ids

    @app_commands.command(name='view', description='View registered user list (admin-only).')
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
                    favorite_game: app_commands.Choice[int] = None,
                    age: int = None):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

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

        users = get_all_users(region=region, favorite_game=favorite_game, age=age)

        if not users:
            return await ctx.edit_original_message(content=messages["users_not_found"])

        embed.title = 'Registered User List'
        embed.description = f'Total **{len(users)}** registered users with the given constraints.\n\n'

        for user in enumerate(users):
            embed.description += f'`{user[0] + 1}.` {ctx.guild.get_member(user[1][0]).mention} - `{user[1][1]}`\n'

        await ctx.edit_original_message(embed=embed)

    @app_commands.command(name='forcelink', description='Force links your Steam profile with the bot (admin-only).')
    @app_commands.guilds(whitelist)
    async def _force_link(self, ctx: discord.Interaction, member: discord.Member, community_id: str):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

        if already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_previously_linked"])

        try:
            # noinspection PyUnresolvedReferences
            steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                        if 'https://steamcommunity.com/id/' not in community_id else community_id)

            if steam_id is None:
                steam_id = community_id

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            steam_id = SteamID(steam_user["steamid"])

            if int(steam_user["steamid"]) in get_steam_ids():
                return await ctx.edit_original_message(content=messages["profile_already_linked"])

        except (requests.HTTPError, IndexError):
            return await ctx.edit_original_message(content=messages["profile_not_found"])

        add_user(member.id, steam_user["steamid"])

        await ctx.edit_original_message(content=messages["profile_link_success"])

        # noinspection PyUnresolvedReferences
        game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

        game_stats = game_stats["playerstats"]["stats"]

        hours = 0

        for game_stat in game_stats:
            if game_stat["name"] == 'total_time_played':
                hours = round(game_stat["value"] / 3600)

        update_hours(member.id, hours)

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                stats = await stats.json()

            if "error" not in stats.keys():
                for role_id in self.mm_rank_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                rank_role = ctx.guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                await member.add_roles(rank_role)

            async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                stats = await stats.json()

            if "error" not in stats.keys():
                for role_id in self.faceit_rank_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in member.roles:
                        await ctx.user.remove_roles(role)

                rank_role = ctx.guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                await member.add_roles(rank_role)

            if "loccountrycode" in steam_user.keys():
                async with session.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}') \
                        as res:
                    res = await res.json()
                update_country(member.id, res[0]["name"]["common"])

                region = res[0]["region"]

                if region == "Americas":
                    region = res[0]["subregion"]

                update_region(member.id, region)

                for role_id in self.region_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                region_role_id = self.region_role_ids[region]

                region_role = ctx.guild.get_role(region_role_id)

                await member.add_roles(region_role)

        return await log_message(ctx, f'`{ctx.user}` force-linked the Steam profile for `{member}`.')

    @app_commands.command(name='forceunlink', description='Force de-links a Steam profile from the bot (admin-only).')
    @app_commands.guilds(whitelist)
    async def _force_unlink(self, ctx: discord.Interaction, member: discord.Member):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

        if already_exists(member.id):
            view = UnlinkConfirm()
            view.ctx = ctx
            view.member = member

            return await ctx.edit_original_message(content='Would you like to proceed?', view=view)

        else:
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

    @app_commands.command(name='forceadd', description='Force adds a member / substitute to a particular team '
                                                       '(admin-only).')
    @app_commands.choices(add_type=[
        app_commands.Choice(name='Member', value=1),
        app_commands.Choice(name='Substitute', value=2),
    ])
    @app_commands.guilds(whitelist)
    async def _force_add(self, ctx: discord.Interaction, member: discord.Member, add_type: app_commands.Choice[int]):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

        if not already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        teams = get_teams_by_captain_id(-1)

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Select Team'
        embed.description = 'Which team would you like to update the logo for?\n'

        _options = list()

        for i, team_details in enumerate(teams, 1):
            embed.description += f'\n`{i}.` {team_details[1]}'

            _options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

        if add_type.value == 1:
            item = TeamMemberForceAdd(options=_options)
            item.ctx = ctx
            item.member = member

        else:
            item = TeamSubstituteForceAdd(options=_options)
            item.ctx = ctx
            item.substitute = member

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Admin(bot))
