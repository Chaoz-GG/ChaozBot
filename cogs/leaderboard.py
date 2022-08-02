import json

from steam.webapi import WebAPI

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.db import sort_lb
from utils.tools import log_message


with open('config.json') as _json_file:
    _data = json.load(_json_file)
    whitelist = _data['whitelist']
    update_frequency = _data['update_frequency']
    steam_key = _data['steam_key']
    sudo_role_ids = _data['sudo_role_ids']
    chaoz_logo_url = _data['chaoz_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["leaderboard"]


class LeaderBoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.lb_channel_id = data['lb_channel_id']

        self.steamAPI = WebAPI(steam_key)

        self.mm_ranks = {
            0: 'Unranked',
            1: 'Silver 1',
            2: 'Silver 2',
            3: 'Silver 3',
            4: 'Silver 4',
            5: 'Silver Elite',
            6: 'Silver Elite Master',
            7: 'Gold Nova 1',
            8: 'Gold Nova 2',
            9: 'Gold Nova 3',
            10: 'Gold Nova Master',
            11: 'Master Guardian 1',
            12: 'Master Guardian 2',
            13: 'Master Guardian Elite',
            14: 'Distinguished Master Guardian',
            15: 'Legendary Eagle',
            16: 'Legendary Eagle Master',
            17: 'Supreme Master First Class',
            18: 'Global Elite'
        }

    # Auto-update leaderboard
    @tasks.loop(hours=update_frequency)
    async def _update_lb(self, channel_id=None):
        guild = self.bot.get_guild(whitelist)
        channel = guild.get_channel(channel_id or self.lb_channel_id)

        if not channel_id:
            with open('data/leaderboard.json') as f:
                try:
                    lb_msgs = json.load(f)

                except json.decoder.JSONDecodeError:
                    lb_msgs = {}

        else:
            lb_msgs = {}

        msgs = []

        for _region in ['North America',
                        'South America',
                        'Europe',
                        'Africa',
                        'Asia',
                        'Oceania']:

            lb = sort_lb(region=_region)

            if not lb:
                continue

            embed = discord.Embed(colour=self.bot.embed_colour)

            embed.set_thumbnail(url=chaoz_logo_url)

            embed.title = f'{_region} LeaderBoard'
            embed.description = ''

            for index, lb_data in enumerate(lb):
                # noinspection PyUnresolvedReferences
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=lb_data[0])["response"]["players"][
                    0]

                guild_user = guild.get_member(lb_data[1])

                embed.description += f'\n`{index + 1}.` ' \
                                     f'[{steam_user["personaname"]}]' \
                                     f'(https://steamcommunity.com/profiles/{lb_data[0]}) ' \
                                     f'({guild_user.mention}) - MM: `{lb_data[2]}`, FaceIT: `{lb_data[3]}`'

            if _region not in lb_msgs.keys():
                msg = await channel.send(embed=embed)

                if not channel_id:
                    with open('data/leaderboard.json', 'w') as f:
                        lb_msgs[_region] = msg.id
                        json.dump(lb_msgs, f)

                msgs.append(msg)

            else:
                msg = await channel.fetch_message(lb_msgs[_region])
                await msg.edit(embed=embed)

        for msg in msgs:
            await msg.pin()

    @app_commands.command(name='leaderboard', description='Show region-wise leaderboard with additional filters!')
    @app_commands.choices(region=[
        app_commands.Choice(name='North America', value=1),
        app_commands.Choice(name='South America', value=2),
        app_commands.Choice(name='Europe', value=3),
        app_commands.Choice(name='Africa', value=4),
        app_commands.Choice(name='Asia', value=5),
        app_commands.Choice(name='Oceania', value=6)
    ])
    @app_commands.choices(mm_rank=[
        app_commands.Choice(name='Unranked', value=0),
        app_commands.Choice(name='Silver 1', value=1),
        app_commands.Choice(name='Silver 2', value=2),
        app_commands.Choice(name='Silver 3', value=3),
        app_commands.Choice(name='Silver 4', value=4),
        app_commands.Choice(name='Silver Elite', value=5),
        app_commands.Choice(name='Silver Elite Master', value=6),
        app_commands.Choice(name='Gold Nova 1', value=7),
        app_commands.Choice(name='Gold Nova 2', value=8),
        app_commands.Choice(name='Gold Nova 3', value=9),
        app_commands.Choice(name='Gold Nova Master', value=10),
        app_commands.Choice(name='Master Guardian 1', value=11),
        app_commands.Choice(name='Master Guardian 2', value=12),
        app_commands.Choice(name='Master Guardian Elite', value=13),
        app_commands.Choice(name='Distinguished Master Guardian', value=14),
        app_commands.Choice(name='Legendary Eagle', value=15),
        app_commands.Choice(name='Legendary Eagle Master', value=16),
        app_commands.Choice(name='Supreme Master First Class', value=17),
        app_commands.Choice(name='Global Elite', value=18)
    ])
    @app_commands.choices(faceit_rank=[
        app_commands.Choice(name='Level 1', value=1),
        app_commands.Choice(name='Level 2', value=2),
        app_commands.Choice(name='Level 3', value=3),
        app_commands.Choice(name='Level 4', value=4),
        app_commands.Choice(name='Level 5', value=5),
        app_commands.Choice(name='Level 6', value=6),
        app_commands.Choice(name='Level 7', value=7),
        app_commands.Choice(name='Level 8', value=8),
        app_commands.Choice(name='Level 9', value=9),
        app_commands.Choice(name='Level 10', value=10)
    ])
    @app_commands.guilds(whitelist)
    async def _leaderboard(self, ctx: discord.Interaction, region: app_commands.Choice[int],
                           mm_rank: app_commands.Choice[int] = None, faceit_rank: app_commands.Choice[int] = None):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        await ctx.response.defer(thinking=True)

        if mm_rank:
            mm_rank = mm_rank.name

        if faceit_rank:
            faceit_rank = faceit_rank.value

        if mm_rank:
            lb = sort_lb(region.name, mm_rank=mm_rank)

        elif faceit_rank:
            lb = sort_lb(region.name, faceit_rank=faceit_rank)

        else:
            lb = sort_lb(region.name)

        if not lb:
            return await ctx.edit_original_message(content=messages["region_stats_unavailable"].format(region.name))

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_thumbnail(url=chaoz_logo_url)

        embed.title = f'{region.name} LeaderBoard'
        embed.description = ''

        for index, lb_data in enumerate(lb):
            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=lb_data[0])["response"]["players"][0]

            guild_user = ctx.guild.get_member(lb_data[1])

            embed.description += f'\n`{index + 1}` ' \
                                 f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{lb_data[0]}) ' \
                                 f'({guild_user.mention})'

            if (mm_rank and not faceit_rank) or (faceit_rank and not mm_rank):
                embed.description += f' - `{lb_data[2]}`'

            else:
                embed.description += f' - MM: `{lb_data[2]}`, FaceIT: `{lb_data[3]}`'

        await ctx.edit_original_message(embed=embed)

    @app_commands.command(name='publish', description='Publish the region-wise leaderboards.')
    @app_commands.guilds(whitelist)
    async def _publish(self, ctx: discord.Interaction, channel: discord.TextChannel = None):
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

        if not channel:
            await self._update_lb()

        else:
            await self._update_lb(channel.id)

        await ctx.edit_original_message(content=messages["leaderboards_published"])

    @commands.Cog.listener()
    async def on_ready(self):
        self._update_lb.start()

    # Update leaderboards on member leaving
    # noinspection PyUnusedLocal
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._update_lb()


async def setup(bot):
    await bot.add_cog(LeaderBoard(bot))
