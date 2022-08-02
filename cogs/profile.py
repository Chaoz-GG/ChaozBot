import json
from datetime import datetime

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

import aiohttp
import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID
from steam.enums import EPersonaState

from utils.tools import make_list_embed, generate_token, log_message
from utils.db import get_steam_ids, get_steam_id, already_exists, remove_user, has_generated_token, initiate_auth, \
    cleanup_auth, get_token, add_user, update_birthday, update_timezone, update_bio, update_favorite_game, \
    update_country, update_region, update_hours


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    steam_key = data['steam_key']
    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']
    chaoz_logo_url = data['chaoz_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["profile"]


class ProfileForm(ui.Modal, title='Profile Update'):
    options = list()

    with open('data/games.json') as f:
        games = json.load(f)

    for abbr, game in games.items():
        options.append(discord.SelectOption(label=game[0], value=abbr))

    birthday = ui.TextInput(label='Birthday', placeholder='DD/MM/YYYY', max_length=10, required=False)
    timezone = ui.TextInput(label='Timezone', placeholder='Check https://bot.chaoz.gg/timezones.json', required=False)
    bio = ui.TextInput(label='Bio',
                       placeholder='Enter your bio ...',
                       style=discord.TextStyle.long,
                       max_length=300,
                       required=False)
    favorite_game = ui.Select(placeholder='Choose your favorite game ...', options=options, max_values=1, min_values=0)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)

        with open('data/games.json') as f:
            games = json.load(f)

        if self.birthday.value:
            birthday = self.birthday.value.replace('/', '')

            try:
                birthday = datetime.strptime(birthday, "%d%m%Y").date()

            except ValueError:
                return await ctx.edit_original_message(content=messages["birthday_invalid"])

            update_birthday(ctx.user.id, birthday)

        if self.timezone.value:
            with open('data/timezones.json') as f:
                timezones = json.load(f)

            if self.timezone.value not in timezones:
                return await ctx.edit_original_message(content=messages["timezone_invalid"])

            update_timezone(ctx.user.id, self.timezone.value)

        if self.bio.value:
            update_bio(ctx.user.id, self.bio.value)

        if self.favorite_game.values:
            update_favorite_game(ctx.user.id, games[self.favorite_game.values[0]][0])

        return await ctx.edit_original_message(content=messages["profile_updated"])


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.steamAPI = WebAPI(steam_key)

        self.mm_rank_role_ids = mm_rank_role_ids
        self.faceit_rank_role_ids = faceit_rank_role_ids
        self.region_role_ids = region_role_ids

    @app_commands.command(name='steam', description='Shows various information about the profile of a steam user.')
    @app_commands.guilds(whitelist)
    async def _steam(self, ctx: discord.Interaction, community_id: str):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        try:
            # noinspection PyUnresolvedReferences
            steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                        if 'https://steamcommunity.com/id/' not in community_id else community_id)

            if steam_id is None:
                steam_id = community_id

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        except (requests.HTTPError, requests.exceptions.HTTPError, IndexError):
            return await ctx.edit_original_message(content=messages["profile_not_found"])

        # noinspection PyUnresolvedReferences
        bans = self.steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steam_id)["players"][0]

        ban_info = {"VAC Banned": bans["VACBanned"], "Community Banned": bans["CommunityBanned"]}

        if bans["VACBanned"]:
            ban_info["VAC Bans"] = bans["NumberOfVACBans"]
            ban_info["Days Since Last VAC Ban"] = bans["DaysSinceLastBan"]

        if steam_user["communityvisibilitystate"] != 3:
            embed = make_list_embed(ban_info, self.bot.embed_colour)

            embed.description = "This profile is private."
            embed.title = steam_user["personaname"]
            embed.colour = self.bot.embed_colour
            embed.url = steam_user["profileurl"]
            embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=steam_user["avatarfull"])

            return await ctx.edit_original_message(embed=embed)

        # noinspection PyUnresolvedReferences
        group_count = len(self.steamAPI.ISteamUser.GetUserGroupList_v1(steamid=steam_id)["response"]["groups"])

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}"
                                   "&include_played_free_games=1%format=json".format(steam_key, steam_id)) as games:
                games = await games.json()
                games = games["response"]

            try:
                games_played = games["game_count"]

            except KeyError:
                games_played = 0

            state = EPersonaState(steam_user["personastate"]).name
            game_name = None

            if "gameid" in steam_user.keys():
                state = "In-game"
                game_id = steam_user["gameid"]
                async with session.get("https://store.steampowered.com/api/appdetails?appids={}".format(game_id)) \
                        as game_name:
                    game_name = await game_name.json()
                    game_name = game_name[game_id]["data"]["name"]

        last_online = None

        try:
            last_online = datetime.fromtimestamp(steam_user["lastlogoff"]).strftime("%B %d, %Y at %I:%M:%S %p")

        except KeyError:
            pass

        creation_date = datetime.fromtimestamp(steam_user["timecreated"]).strftime("%B %d, %Y at %I:%M:%S %p")
        fields = {"Status": state, "Created on": creation_date,
                  "Group Count": group_count, "Games Owned": games_played}

        if state == EPersonaState.Offline.name:
            if last_online is not None:
                fields["Last Online"] = last_online

        if game_name:
            fields["Currently Playing"] = game_name

        fields.update(ban_info)
        embed = make_list_embed(fields, self.bot.embed_colour)
        embed.title = steam_user["personaname"]
        embed.colour = self.bot.embed_colour
        embed.url = steam_user["profileurl"]
        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
        embed.set_thumbnail(url=steam_user["avatarfull"])

        await ctx.edit_original_message(embed=embed)

    @app_commands.command(name='link', description='Links your Steam profile with the bot.')
    @app_commands.guilds(whitelist)
    async def _link(self, ctx: discord.Interaction, community_id: str):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if already_exists(ctx.user.id):
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

        if not has_generated_token(ctx.user.id):
            _token = generate_token()
            initiate_auth(ctx.user.id, _token)

            return await ctx.edit_original_message(content=messages["auth_add_token"].format(_token))

        else:
            _token = get_token(ctx.user.id)

            if steam_user["personaname"].endswith(_token):
                add_user(ctx.user.id, steam_user["steamid"])
                cleanup_auth(ctx.user.id)

                await ctx.edit_original_message(content=messages["profile_link_success"])

                # noinspection PyUnresolvedReferences
                game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

                game_stats = game_stats["playerstats"]["stats"]

                hours = 0

                for game_stat in game_stats:
                    if game_stat["name"] == 'total_time_played':
                        hours = round(game_stat["value"] / 3600)

                update_hours(ctx.user.id, hours)

                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                        stats = await stats.json()

                    if "error" not in stats.keys():
                        for role_id in self.mm_rank_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        rank_role = ctx.guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                        await ctx.user.add_roles(rank_role)

                    async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                        stats = await stats.json()

                    if "error" not in stats.keys():
                        for role_id in self.faceit_rank_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        rank_role = ctx.guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                        await ctx.user.add_roles(rank_role)

                    if "loccountrycode" in steam_user.keys():
                        async with session.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}') \
                                as res:
                            res = await res.json()
                        update_country(ctx.user.id, res[0]["name"]["common"])

                        region = res[0]["region"]

                        if region == "Americas":
                            region = res[0]["subregion"]

                        update_region(ctx.user.id, region)

                        for role_id in self.region_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        region_role_id = self.region_role_ids[region]

                        region_role = ctx.guild.get_role(region_role_id)

                        await ctx.user.add_roles(region_role)

                return await log_message(ctx, f'`{ctx.user}` have linked their Steam profile.')

            else:
                return await ctx.edit_original_message(content=messages["auth_token_undetected"].format(_token))

    @app_commands.command(name='unlink', description='De-links your Steam profile from the bot.')
    @app_commands.guilds(whitelist)
    async def _unlink(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if already_exists(ctx.user.id):
            steam_id = get_steam_id(ctx.user.id)

            remove_user(ctx.user.id, steam_id)

            return await ctx.edit_original_message(content=messages["profile_unlink_success"])

        else:
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

    @app_commands.command(name='profile', description='Update your profile.')
    @app_commands.guilds(whitelist)
    async def _profile(self, ctx: discord.Interaction):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if not already_exists(ctx.user.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        modal = ProfileForm()
        await ctx.response.send_modal(modal)
        await modal.wait()

    @app_commands.command(name='country', description='Sets your country.')
    @app_commands.guilds(whitelist)
    async def _country(self, ctx: discord.Interaction, *, country: str):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if already_exists(ctx.user.id):
            steam_id = get_steam_id(ctx.user.id)

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            if "loccountrycode" in steam_user.keys():
                return await ctx.edit_original_message(content=messages["country_link_warning"])

            if len(country) > 25:
                return await ctx.edit_original_message(content=messages["country_too_long"])

            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://restcountries.com/v3.1/name/{country}') as res:
                    if res.status == 404:
                        return await ctx.edit_original_message(content='Invalid country name.')

                    res = await res.json()

            update_country(ctx.user.id, res[0]["name"]["common"])

            region = res[0]["region"]

            if region == "Americas":
                region = res[0]["subregion"]

            update_region(ctx.user.id, region)

            for role_id in self.region_role_ids.values():
                role = ctx.guild.get_role(role_id)

                if role in ctx.user.roles:
                    await ctx.user.remove_roles(role)

            region_role_id = self.region_role_ids[region]

            region_role = ctx.guild.get_role(region_role_id)

            await ctx.user.add_roles(region_role)

            return await ctx.edit_original_message(content=messages["country_updated"])

        else:
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

    @app_commands.command(name='inv',
                          description='Calculates the inventory value of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _inv(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if member is None:
            member = ctx.user

        if not already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:5000/inventory/{steam_id}') as inv:
                    inv = await inv.json()

            if "error" in inv.keys():
                return await ctx.edit_original_message(content=messages["inventory_error"])

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            embed = discord.Embed(colour=self.bot.embed_colour)

            embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=steam_user["avatarfull"])

            embed.title = steam_user["personaname"]
            embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

            embed.description = f'`{inv["item_count"]}` items worth `${inv["value"]}`.'

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(label='View Inventory',
                                  url=f'https://steamcommunity.com/profiles/{steam_id}/inventory/')
            )

            await ctx.edit_original_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Profile(bot))
