import json
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

import aiohttp
import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID
from steam.enums import EPersonaState

from utils.tools import make_list_embed, generate_token
from utils.db import get_steam_ids, get_steam_id, already_exists, remove_user, has_generated_token, initiate_auth, \
    cleanup_auth, get_token, add_user, update_bio, update_country, update_region, update_hours


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    log_channel_id = data['log_channel_id']
    steam_key = data['steam_key']
    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']


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

        try:
            # noinspection PyUnresolvedReferences
            steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                        if 'https://steamcommunity.com/id/' not in community_id else community_id)

            if steam_id is None:
                steam_id = community_id

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        except (requests.HTTPError, requests.exceptions.HTTPError, IndexError):
            return await ctx.edit_original_message(content='No such user found! Make sure you are using a valid '
                                                           'Steam community ID / URL.')

        # noinspection PyUnresolvedReferences
        bans = self.steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steam_id)["players"][0]

        ban_info = {"VAC Banned": bans["VACBanned"], "Community Banned": bans["CommunityBanned"]}

        if bans["VACBanned"]:
            ban_info["VAC Bans"] = bans["NumberOfVACBans"]
            ban_info["Days Since Last VAC Ban"] = bans["DaysSinceLastBan"]

        if steam_user["communityvisibilitystate"] != 3:
            embed = make_list_embed(ban_info)

            embed.description = "This profile is private."
            embed.title = steam_user["personaname"]
            embed.colour = self.bot.embed_colour
            embed.url = steam_user["profileurl"]
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
        embed = make_list_embed(fields)
        embed.title = steam_user["personaname"]
        embed.colour = self.bot.embed_colour
        embed.url = steam_user["profileurl"]
        embed.set_thumbnail(url=steam_user["avatarfull"])

        await ctx.edit_original_message(embed=embed)

    @app_commands.command(name='link', description='Links your Steam profile with the bot.')
    @app_commands.guilds(whitelist)
    async def _link(self, ctx: discord.Interaction, community_id: str):
        await ctx.response.defer(thinking=True, ephemeral=True)

        if not community_id:
            return await ctx.edit_original_message(content='Please provide your Steam community ID/URL.')

        if already_exists(ctx.user.id):
            return await ctx.edit_original_message(
                content='You have already linked your Steam profile, if you would like '
                        'to link a new Steam account, first use the `/unlink` command '
                        'and then link the new account.')

        try:
            # noinspection PyUnresolvedReferences
            steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                        if 'https://steamcommunity.com/id/' not in community_id else community_id)

            if steam_id is None:
                steam_id = community_id

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            if int(steam_user["steamid"]) in get_steam_ids():
                return await ctx.edit_original_message(content='This Steam account has already been linked '
                                                               'by another user.')

        except (requests.HTTPError, IndexError):
            message = 'No such user found ... make sure you are using a valid Steam community ID/URL!'
            return await ctx.edit_original_message(content=message)

        if not has_generated_token(ctx.user.id):
            _token = generate_token()
            initiate_auth(ctx.user.id, _token)

            return await ctx.edit_original_message(
                content=f'Please add `{_token}` to the end of your Steam profile name '
                        'and run this command again.')

        else:
            _token = get_token(ctx.user.id)

            if steam_user["personaname"].endswith(_token):
                add_user(ctx.user.id, steam_user["steamid"])
                cleanup_auth(ctx.user.id)

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

                        await ctx.edit_original_message(content='Verification successful! You may now remove the token '
                                                                'from your profile name on Steam.')

                    else:
                        await ctx.edit_original_message(content='Verification successful! You may now remove the token '
                                                                'from your profile name on Steam.'
                                                                '\n\n**NOTE:** You do not have a country listed '
                                                                'on your Steam profile.'
                                                                ' Please use the `/country` command to update it now.')

                log_channel = ctx.guild.get_channel(log_channel_id)

                return await log_channel.send(f'`{ctx.user}` have linked their Steam profile.')

            else:
                return await ctx.edit_original_message(
                    content=f'Verification token (`{_token}`) could not be detected, '
                            'please make sure the changes have been saved.')

    @app_commands.command(name='unlink', description='De-links your Steam profile from the bot.')
    @app_commands.guilds(whitelist)
    async def _unlink(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        if already_exists(ctx.user.id):
            steam_id = get_steam_id(ctx.user.id)

            remove_user(ctx.user.id, steam_id)

            return await ctx.edit_original_message(content='Your Steam account has been unlinked.')

        else:
            return await ctx.edit_original_message(content='You have not linked your Steam account yet.')

    @app_commands.command(name='bio', description='Sets your bio.')
    @app_commands.guilds(whitelist)
    async def _bio(self, ctx: discord.Interaction, *, bio: str):
        await ctx.response.defer(thinking=True)

        if already_exists(ctx.user.id):

            if len(bio) > 200:
                return await ctx.edit_original_message(content='Bio cannot be more than 200 characters.')

            update_bio(ctx.user.id, bio)

            return await ctx.edit_original_message(content='Your bio has been updated.')

        else:
            return await ctx.edit_original_message(content='You have not linked your Steam account yet. '
                                                           'Please do so first with the `/link` command.')

    @app_commands.command(name='country', description='Sets your country.')
    @app_commands.guilds(whitelist)
    async def _country(self, ctx: discord.Interaction, *, country: str):
        await ctx.response.defer(thinking=True)

        if already_exists(ctx.user.id):
            steam_id = get_steam_id(ctx.user.id)

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            if "loccountrycode" in steam_user.keys():
                return await ctx.edit_original_message(
                    content='Only users without a country listed on their Steam profile '
                            'can use this command.')

            if len(country) > 25:
                return await ctx.edit_original_message(content='Country name cannot be more than 25 characters.')

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

            return await ctx.edit_original_message(content='Your country has been updated.')

        else:
            return await ctx.edit_original_message(content='You have not linked your Steam account yet.'
                                                           'Please do so first with the `/link` command.')

    @app_commands.command(name='inv',
                          description='Calculates the inventory value of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _inv(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        if member is None:
            member = ctx.user

        if not already_exists(member.id):
            return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet. '
                                                           '(use `/link`)')

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:5000/inventory/{steam_id}') as inv:
                    inv = await inv.json()

            if "error" in inv.keys():
                return await ctx.edit_original_message(content='No inventory details found for this user.')

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            embed = discord.Embed(colour=self.bot.embed_colour)

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
