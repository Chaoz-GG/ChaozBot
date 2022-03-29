from discord.ext import commands, tasks

import json

import requests
import aiohttp
from steam.webapi import WebAPI

from utils.db import get_steam_ids, remove_user, get_user_id, update_country, update_region, update_hours

with open('config.json') as _json_file:
    _data = json.load(_json_file)
    update_frequency = _data['update_frequency']
    steam_key = _data['steam_key']


class AutoUpdater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.steamAPI = WebAPI(steam_key)

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.whitelist = data['whitelist']
            self.mm_rank_role_ids = data['mm_rank_role_ids']
            self.faceit_rank_role_ids = data['faceit_rank_role_ids']
            self.region_role_ids = data['region_role_ids']

    # Auto-update stats
    @tasks.loop(hours=update_frequency)
    async def _update_stats(self):
        guild = self.bot.get_guild(self.whitelist)

        for steam_id in get_steam_ids():
            user_id = get_user_id(steam_id)
            member = guild.get_member(user_id)

            if not member:
                remove_user(user_id, steam_id)
                continue

            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:5000/stats/update/mm/{steam_id}'):
                    pass

                async with session.get(f'http://localhost:5000/stats/update/faceit/{steam_id}'):
                    pass

                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" not in stats.keys():
                        for role_id in self.mm_rank_role_ids.values():
                            role = guild.get_role(role_id)

                            if role in member.roles:
                                await member.remove_roles(role)

                        rank_role = guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                        await member.add_roles(rank_role)

                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" not in stats.keys():
                        for role_id in self.faceit_rank_role_ids.values():
                            role = guild.get_role(role_id)

                            if role in member.roles:
                                await member.remove_roles(role)

                        rank_role = guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                        await member.add_roles(rank_role)

            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            if "loccountrycode" in steam_user.keys():
                res = requests.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}').json()
                update_country(member.id, res[0]["name"]["common"])

                region = res[0]["region"]

                if region == "Americas":
                    region = res[0]["subregion"]

                update_region(member.id, region)

                for role_id in self.region_role_ids.values():
                    role = guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                region_role_id = self.region_role_ids[region]

                region_role = guild.get_role(region_role_id)

                await member.add_roles(region_role)

            # noinspection PyUnresolvedReferences
            game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

            game_stats = game_stats["playerstats"]["stats"]

            hours = 0

            for game_stat in game_stats:
                if game_stat["name"] == 'total_time_played':
                    hours = round(game_stat["value"] / 3600)

            update_hours(member.id, hours)

    @commands.Cog.listener()
    async def on_ready(self):
        self._update_stats.start()


async def setup(bot):
    await bot.add_cog(AutoUpdater(bot))
