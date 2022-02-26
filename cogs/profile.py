#!/usr/bin/python3

from discord.ext import commands

import json
from datetime import datetime

import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID
from steam.enums import EPersonaState


from utils.tools import make_list_embed, generate_token, reply_message
from utils.db import already_exists, has_generated_token, initiate_auth, cleanup_auth, get_token, add_user, \
    remove_user, update_bio, update_country, get_steam_id, get_steam_ids


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.key = data['steam_key']

        self.steamAPI = WebAPI(self.key)

    @commands.command(name='steam')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _steam(self, ctx, community_id):

        if not community_id:
            return await reply_message(ctx=ctx,
                                       content='Please provide your Steam community ID/URL.',
                                       emoji=self.bot.emoji2)

        async with ctx.typing():
            try:
                # noinspection PyUnresolvedReferences
                steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                            if 'https://steamcommunity.com/id/' not in community_id else community_id)

                if steam_id is None:
                    steam_id = community_id

                # noinspection PyUnresolvedReferences
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            except (requests.HTTPError, IndexError):
                message = 'No such user found ... make sure you are using a valid Steam community ID/URL!'
                return await reply_message(ctx=ctx, content=message, emoji=self.bot.emoji2)

            # noinspection PyUnresolvedReferences
            bans = self.steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steam_id)["players"][0]

            vac_banned = bans["VACBanned"]
            community_banned = bans["CommunityBanned"]

            ban_info = {"VAC Banned": vac_banned, "Community Banned": community_banned}

            if vac_banned:
                ban_info["VAC Bans"] = bans["NumberOfVACBans"]
                ban_info["Days Since Last VAC Ban"] = bans["DaysSinceLastBan"]

            if steam_user["communityvisibilitystate"] != 3:
                embed = make_list_embed(ban_info)

                embed.description = "This profile is private."
                embed.title = steam_user["personaname"]
                embed.colour = self.bot.embed_colour
                embed.url = steam_user["profileurl"]
                embed.set_thumbnail(url=steam_user["avatarfull"])

                return await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji1)

            # noinspection PyUnresolvedReferences
            group_count = len(self.steamAPI.ISteamUser.GetUserGroupList_v1(steamid=steam_id)["response"]["groups"])

            games = requests.get(
                "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
                "?key={}&steamid={}&include_played_free_games=1%format=json".format(
                    self.key, steam_id)).json()["response"]

            try:
                games_played = games["game_count"]

            except KeyError:
                games_played = 0

            state = EPersonaState(steam_user["personastate"]).name
            game_name = None

            if "gameid" in steam_user.keys():
                state = "In-game"
                game_id = steam_user["gameid"]
                game_name = requests.get("https://store.steampowered.com/api/appdetails?appids={}"
                                         .format(game_id)).json()[game_id]["data"]["name"]

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

            await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji1)

    @commands.command(name='link')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _link(self, ctx, community_id=None):

        if not community_id:
            return await reply_message(ctx=ctx,
                                       content='Please provide your Steam community ID/URL.',
                                       emoji=self.bot.emoji2)

        if already_exists(ctx.author.id):
            return await reply_message(ctx=ctx,
                                       content='You have already linked your Steam profile, if you would like to link '
                                               'a new Steam account, first use the `unlink` command and then link the '
                                               'new account.',
                                       emoji=self.bot.emoji2)

        async with ctx.typing():
            try:
                # noinspection PyUnresolvedReferences
                steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                            if 'https://steamcommunity.com/id/' not in community_id else community_id)

                if steam_id is None:
                    steam_id = community_id

                # noinspection PyUnresolvedReferences
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                if int(steam_user["steamid"]) in get_steam_ids():
                    return await reply_message(ctx=ctx,
                                               content='This Steam account has already been linked by another user.',
                                               emoji=self.bot.emoji2)

            except (requests.HTTPError, IndexError):
                message = 'No such user found ... make sure you are using a valid Steam community ID/URL!'
                return await reply_message(ctx=ctx, content=message, emoji=self.bot.emoji2)

            if not has_generated_token(ctx.author.id):
                token = generate_token()
                initiate_auth(ctx.author.id, token)

                return await reply_message(ctx=ctx,
                                           content=f'Please add `{token}` to the end of your Steam profile name '
                                                   f'and run this command again.',
                                           emoji=self.bot.emoji1)

            else:
                token = get_token(ctx.author.id)

                if steam_user["personaname"].endswith(token):
                    add_user(ctx.author.id, steam_user["steamid"])
                    cleanup_auth(ctx.author.id)

                    return await reply_message(ctx=ctx,
                                               content='Verification successful! '
                                                       'You may now remove the token from your profile name on Steam.',
                                               emoji=self.bot.emoji1)

                else:
                    return await reply_message(ctx=ctx,
                                               content=f'Verification token (`{token}`) could not be detected, '
                                                       'please make sure the changes have been saved.',
                                               emoji=self.bot.emoji1)

    @commands.command(name='unlink')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _unlink(self, ctx):

        if already_exists(ctx.author.id):
            steam_id = get_steam_id(ctx.author.id)

            remove_user(ctx.author.id, steam_id)

            return await reply_message(ctx=ctx,
                                       content='Your Steam account has been unlinked.',
                                       emoji=self.bot.emoji1)

        else:
            return await reply_message(ctx=ctx,
                                       content='You have not linked your Steam account yet.',
                                       emoji=self.bot.emoji2)

    @commands.command(name='bio')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _bio(self, ctx, *, bio: str):

        if already_exists(ctx.author.id):

            if len(bio) > 200:
                return await reply_message(ctx=ctx,
                                           content='Bio cannot be more than 200 characters.',
                                           emoji=self.bot.emoji2)

            update_bio(ctx.author.id, bio)

            return await reply_message(ctx=ctx,
                                       content='Your bio has been updated.',
                                       emoji=self.bot.emoji1)

        else:
            return await reply_message(ctx=ctx,
                                       content='You have not linked your Steam account yet.'
                                               'Please do so first with the `$link steam_id` command.',
                                       emoji=self.bot.emoji2)

    @commands.command(name='country')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _country(self, ctx, *, country: str):

        if already_exists(ctx.author.id):

            if len(country) > 25:
                return await reply_message(ctx=ctx,
                                           content='Country name cannot be more than 25 characters.',
                                           emoji=self.bot.emoji2)

            res = requests.get(f'https://restcountries.com/v3.1/name/{country}')

            if res.status_code == 404:
                return await reply_message(ctx=ctx,
                                           content='Invalid country name.',
                                           emoji=self.bot.emoji2)

            res = res.json()

            update_country(ctx.author.id, res[0]["name"]["common"])

            return await reply_message(ctx=ctx,
                                       content='Your country has been updated.',
                                       emoji=self.bot.emoji1)

        else:
            return await reply_message(ctx=ctx,
                                       content='You have not linked your Steam account yet.'
                                               'Please do so first with the `$link steam_id` command.',
                                       emoji=self.bot.emoji2)


def setup(bot):
    bot.add_cog(Profile(bot))
