from discord.ext import commands, tasks

import json

import aiohttp
from steam.webapi import WebAPI

from utils.db import get_steam_ids, remove_user, get_user_id, update_country, update_region, update_hours
from utils.tools import log_message

with open('config.json') as _json_file:
    _data = json.load(_json_file)
    update_frequency = _data['update_frequency']
    steam_key = _data['steam_key']


class AutoUpdater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create a steam WebAPI object
        self.steamAPI = WebAPI(steam_key)

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.whitelist = data['whitelist']
            self.mm_rank_role_ids = data['mm_rank_role_ids']
            self.faceit_rank_role_ids = data['faceit_rank_role_ids']
            self.region_role_ids = data['region_role_ids']

    # Auto-update stats
    @tasks.loop(hours=update_frequency)
    async def update_stats(self):
        guild = self.bot.get_guild(self.whitelist)

        # Fetch all user entries from the database
        steam_ids = get_steam_ids()

        for steam_id in steam_ids:
            user_id = get_user_id(steam_id)
            member = guild.get_member(user_id)

            # Remove entry from the database if the user has  left the server
            if not member:
                remove_user(user_id, steam_id)
                continue

            await log_message(member, f'Auto-updating stats for `{member}`. This may take a while...')

            async with aiohttp.ClientSession() as session:
                # Update matchmaking stats for the user
                async with session.get(f'http://localhost:5000/stats/update/mm/{steam_id}'):
                    pass

                # Update FaceIT stats for the user
                async with session.get(f'http://localhost:5000/stats/update/faceit/{steam_id}'):
                    pass

                # Fetch matchmaking stats for the user, if found
                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" not in stats.keys():
                        # Remove all rank roles
                        for role_id in self.mm_rank_role_ids.values():
                            role = guild.get_role(role_id)

                            if role in member.roles:
                                await member.remove_roles(role)

                        # Fetch the relevant rank role
                        rank_role = guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                        # Add the rank role to the user
                        await member.add_roles(rank_role)

                # Fetch matchmaking stats for the user, if found
                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" not in stats.keys():
                        # Remove all rank roles
                        for role_id in self.faceit_rank_role_ids.values():
                            role = guild.get_role(role_id)

                            if role in member.roles:
                                await member.remove_roles(role)

                        # Fetch the relevant rank role
                        rank_role = guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                        # Add the rank role to the user
                        await member.add_roles(rank_role)

            # Fetch the Steam user instance
            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            if "loccountrycode" in steam_user.keys():
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}') \
                            as res:
                        res = await res.json()

                # Update the user's country in the database
                update_country(member.id, res[0]["name"]["common"])

                region = res[0]["region"]

                if region == "Americas":
                    region = res[0]["subregion"]

                # Determine and update the user's region in the database
                update_region(member.id, region)

                # Remove all region roles
                for role_id in self.region_role_ids.values():
                    role = guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                region_role_id = self.region_role_ids[region]

                # Fetch the relevant region role
                region_role = guild.get_role(region_role_id)

                # Add the region role to the user
                await member.add_roles(region_role)

            # Fetch the CSGO (app 730) stats for the user
            # noinspection PyUnresolvedReferences
            game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

            game_stats = game_stats["playerstats"]["stats"]

            hours = 0

            for game_stat in game_stats:
                if game_stat["name"] == 'total_time_played':
                    hours = round(game_stat["value"] / 3600)

            # Update the user's total hours played in the database
            update_hours(member.id, hours)

            await log_message(member, f'Auto-update of stats for `{member}` complete.')

    @update_stats.before_loop
    async def _before_update_stats(self):
        # Wait until the bot is ready before starting the task
        await self.bot.wait_until_ready()

    async def cog_load(self) -> None:
        # Start the task when the cog is loaded
        self.update_stats.start()

    async def cog_unload(self) -> None:
        # Cancel the task when the cog is unloaded
        self.update_stats.cancel()


async def setup(bot):
    await bot.add_cog(AutoUpdater(bot))
