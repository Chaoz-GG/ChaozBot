import json
import string
import random
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

import aiohttp
from steam.webapi import WebAPI
from PIL import Image, ImageFont, ImageDraw

from utils.tools import split_string, log_message
from utils.db import get_steam_id, already_exists, get_bio, get_country, update_country, update_region, update_hours

with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']
    update_frequency = data['update_frequency']
    steam_key = data['steam_key']
    sudo_role_ids = data['sudo_role_ids']
    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']
    chaoz_logo_url = data['chaoz_logo_url']
    steam_logo_url = data['steam_logo_url']
    faceit_logo_url = data['faceit_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["statistics"]


class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create a Steam WebAPI instance
        self.steamAPI = WebAPI(steam_key)

        self.update_frequency = update_frequency

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

        self.stats_text_color = '#ffffff'
        self.font = 'assets/fonts/arial.ttf'
        self.title_font = 'assets/fonts/Audiowide.ttf'
        self.bio_font = 'assets/fonts/DejaVuSans.ttf'

        self.mm_rank_role_ids = mm_rank_role_ids
        self.faceit_rank_role_ids = faceit_rank_role_ids
        self.region_role_ids = region_role_ids

    @app_commands.command(name='mmstats',
                          description='Shows the matchmaking statistics of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _mm_stats(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if member is None:
            member = ctx.user

        # Check if the user has linked their Steam account with the bot first
        if not already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                # Fetch the matchmaking stats of the user
                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                if "error" in stats.keys():
                    return await ctx.edit_original_message(content=messages["mm_stats_not_found"])

                # noinspection PyUnresolvedReferences
                # Fetch the Steam profile instance of the user
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                embed = discord.Embed(colour=self.bot.embed_colour)

                embed.title = steam_user["personaname"]
                embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

                embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

                # Load the card base image from local assets
                base = Image.open('assets/images/profile-base.png')
                base = base.convert('RGB')

                _new = base.copy()

                # Create an ImageDraw instance for the base image
                new = ImageDraw.Draw(_new)

                mm_rank = list(self.mm_ranks.keys())[list(self.mm_ranks.values()).index(stats["rank"])]

                # Load the rank image from local assets
                mm_rank_image = Image.open(f'assets/images/ranks/matchmaking/{mm_rank}.png')
                _new.paste(mm_rank_image, (85, 165))

                async with session.get(f'{steam_user["avatarfull"]}') as res:
                    # Load the Steam avatar of the user
                    im = Image.open(BytesIO(await res.read()))

                im = im.convert("RGBA")
                im = im.resize((200, 200))
                big_size = (im.size[0] * 3, im.size[1] * 3)
                # Create a circular mask for the avatar
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(im.size, Image.ANTIALIAS)
                im.putalpha(mask)

                _new.paste(im, (836, 62), im)

                country = get_country(member.id)

                if country:
                    async with session.get(f'https://restcountries.com/v3.1/name/{get_country(member.id)}') as res:
                        res = await res.json()
                        country_code = res[0]["cca2"].lower()

                    async with session.get(f'https://flagcdn.com/32x24/{country_code}.png') as res:
                        # Fetch the country flag image of user
                        flag = Image.open(BytesIO(await res.read()))

                    flag = flag.convert("RGBA")

                    _new.paste(flag, (820, 370))

                else:
                    country = "Country not set."

                __country = f"""Country:       {country}"""

                new.text((20, 20), 'Matchmaking Stats',
                         font=ImageFont.truetype(self.title_font, 45),
                         fill='#292929')

                _two = f"""ADR: {stats["adr"]}"""

                _three = f"""K/D: {stats["kpd"]}\nHLTV Rating: {stats["rating"]}\nClutch%: {stats["clutch"]}"""

                _four = f"""Best Weapon: {stats["best_weapon"]}"""

                _five = f"""HS%: {stats["hs"]}\nWin Rate: {stats["win_rate"]}"""

                _six = f"""Most Successful Map:
{stats["most_successful_map"]}
Most Played Map:
{stats["most_played_map"]}"""

                __bio = get_bio(member.id)

                if __bio:
                    __bio = split_string(text=__bio, limit=35)

                    __bio = '\n'.join(__bio)

                else:
                    __bio = "Bio not set."

                new.text((460, 185), _two, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((55, 330), _three, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((380, 330), _four, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((55, 530), _five, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((390, 530), _six, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)
                new.text((720, 410), __bio, font=ImageFont.truetype(self.bio_font, 25), fill=self.stats_text_color)
                new.text((720, 365), __country, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)

                # Generate a random file name
                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

                # Create a buffer for the image
                buffer = BytesIO()
                _new.save(buffer, format="PNG")
                buffer.seek(0)

                # Convert the buffer to a Discord file object
                file = discord.File(buffer, filename=f'{file_name}.png')

                embed.set_image(url=f'attachment://{file_name}.png')

                embed.set_footer(text=f'Matchmaking | Stats are updated every {self.update_frequency} hours.',
                                 icon_url=steam_logo_url)

                # Remove all the rank roles of the user
                for role_id in self.mm_rank_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                # Fetch the relevant rank role of the user
                rank_role = ctx.guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                # Add the relevant rank role to the user
                await member.add_roles(rank_role)

                await ctx.edit_original_message(attachments=[file], embed=embed)

    @app_commands.command(name='faceitstats',
                          description='Shows the FaceIT statistics of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _faceit_stats(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if member is None:
            member = ctx.user

        # Check if the user has linked their Steam account with the bot first
        if not already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                # Fetch the FaceIT stats of the user, if exists
                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    stats = await stats.json()

                if "error" in stats.keys():
                    return await ctx.edit_original_message(content=messages["faceit_stats_not_found"])

                # noinspection PyUnresolvedReferences
                # Fetch the Steam profile instance of the user
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                embed = discord.Embed(colour=self.bot.embed_colour)

                embed.title = steam_user["personaname"]
                embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

                embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)

                # Load the rank card base image from local assets
                base = Image.open('assets/images/profile-base.png')
                base = base.convert('RGB')

                _new = base.copy()

                # Create an ImageDraw instance for the base image
                new = ImageDraw.Draw(_new)

                # Load the FaceIT rank image from local assets
                faceit_rank_image = Image.open(f'assets/images/ranks/faceit/{stats["rank"]}.png')

                faceit_rank_image = faceit_rank_image.convert("RGBA")
                big_size = (faceit_rank_image.size[0] * 3, faceit_rank_image.size[1] * 3)
                # Create a circular mask for the FaceIT rank image
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(faceit_rank_image.size, Image.ANTIALIAS)
                faceit_rank_image.putalpha(mask)

                _new.paste(faceit_rank_image, (135, 165), faceit_rank_image)

                async with session.get(f'{steam_user["avatarfull"]}') as res:
                    # Load the Steam avatar of the user and wrap it into a BytesIO object
                    im = Image.open(BytesIO(await res.read()))

                im = im.convert("RGBA")
                im = im.resize((200, 200))
                big_size = (im.size[0] * 3, im.size[1] * 3)
                # Create a circular mask for the Steam avatar
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(im.size, Image.ANTIALIAS)
                im.putalpha(mask)

                _new.paste(im, (836, 62), im)

                country = get_country(member.id)

                if country:
                    # Get the CCA2 country code of the user from Rest Countries API
                    async with session.get(f'https://restcountries.com/v3.1/name/{get_country(member.id)}') as res:
                        res = await res.json()
                        country_code = res[0]["cca2"].lower()

                    async with session.get(f'https://flagcdn.com/32x24/{country_code}.png') as res:
                        # Load the country flag image of the user and wrap it into a BytesIO object
                        flag = Image.open(BytesIO(await res.read()))

                    flag = flag.convert("RGBA")

                    _new.paste(flag, (820, 370))

                else:
                    country = "Country not set."

                __country = f"""Country:       {country}"""

                new.text((20, 20), 'FaceIT Stats',
                         font=ImageFont.truetype(self.title_font, 45),
                         fill='#292929')

                _two = f"""ELO: {stats["elo"]}"""

                _three = f"""K/D: {stats["kpd"]}\n\nHLTV Rating: {stats["rating"]}"""

                _four = f"""Matches: {stats["matches"]}"""

                _five = f"""HS%: {stats["hs"]}\n\nWin Rate: {stats["win_rate"]}"""

                _six = f"""Most Successful Map:
{stats["most_successful_map"]}
Most Played Map:
{stats["most_played_map"]}"""

                __bio = get_bio(member.id)

                if __bio:
                    __bio = split_string(text=__bio, limit=35)

                    __bio = '\n'.join(__bio)

                else:
                    __bio = "Bio not set."

                new.text((450, 185), _two, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((55, 340), _three, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((420, 375), _four, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((55, 540), _five, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((390, 530), _six, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)
                new.text((720, 410), __bio, font=ImageFont.truetype(self.bio_font, 25), fill=self.stats_text_color)
                new.text((720, 365), __country, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)

                # Generate a random file name
                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

                # Create a BytesIO object to store the image
                buffer = BytesIO()
                _new.save(buffer, format="PNG")
                buffer.seek(0)

                # Convert the buffer into a discord.File object
                file = discord.File(buffer, filename=f'{file_name}.png')

                embed.set_image(url=f'attachment://{file_name}.png')

                embed.set_footer(text=f'FaceIT | Stats are updated every {update_frequency} hours.',
                                 icon_url=faceit_logo_url)

                # Remove all FaceIT rank roles from the user
                for role_id in self.faceit_rank_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in member.roles:
                        await member.remove_roles(role)

                # Fetch the relevant FaceIT rank role from the user's FaceIT rank
                rank_role = ctx.guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                # Add the FaceIT rank role to the user
                await member.add_roles(rank_role)

                await ctx.edit_original_message(attachments=[file], embed=embed)

    @app_commands.command(name='update',
                          description='Updates the CSGO Matchmaking / FaceIT statistics of the user, if available.')
    @app_commands.guilds(whitelist)
    async def _update(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Bypass for the sudo (administrative) roles set in the config
        sudo_roles = []

        for sudo_role_id in sudo_role_ids:
            sudo_roles.append(ctx.guild.get_role(sudo_role_id))

        for sudo_role in sudo_roles:
            if sudo_role in ctx.user.roles:
                break

        else:
            return await ctx.edit_original_message(content=messages["admin_only"])

        # If no member is specified, use the author of the command
        if not member:
            member = ctx.user

        # Check if the user has linked his Steam account with the bot first
        if not already_exists(member.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                # Request a matchmaking stats update for the user
                async with session.get(f'http://localhost:5000/stats/update/mm/{steam_id}'):
                    pass

                # Request a FaceIT stats update for the user
                async with session.get(f'http://localhost:5000/stats/update/faceit/{steam_id}'):
                    pass

                # Fetch the matchmaking stats of the user
                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                if "error" not in stats.keys():
                    # Remove all the matchmaking rank roles from the user
                    for role_id in self.mm_rank_role_ids.values():
                        role = ctx.guild.get_role(role_id)

                        if role in member.roles:
                            await member.remove_roles(role)

                    # Fetch the relevant matchmaking rank role from the user's matchmaking rank
                    rank_role = ctx.guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                    # Add the matchmaking rank role to the user
                    await member.add_roles(rank_role)

                # Fetch the FaceIT stats of the user, if found
                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    stats = await stats.json()

                if "error" not in stats.keys():
                    # Remove all the FaceIT rank roles from the user
                    for role_id in self.faceit_rank_role_ids.values():
                        role = ctx.guild.get_role(role_id)

                        if role in member.roles:
                            await member.remove_roles(role)

                    # Fetch the relevant FaceIT rank role from the user's FaceIT rank
                    rank_role = ctx.guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                    # Add the FaceIT rank role to the user
                    await member.add_roles(rank_role)

                # noinspection PyUnresolvedReferences
                # Fetch the user's Steam profile instance
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                if "loccountrycode" in steam_user.keys():
                    # Fetch the user's country information
                    async with session.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}') \
                            as res:
                        res = await res.json()

                    # Update the user's country name in the database
                    update_country(member.id, res[0]["name"]["common"])

                    region = res[0]["region"]

                    if region == "Americas":
                        region = res[0]["subregion"]

                    # Update the user's region name in the database
                    update_region(member.id, region)

                    # Remove all the region roles from the user
                    for role_id in self.region_role_ids.values():
                        role = ctx.guild.get_role(role_id)

                        if role in member.roles:
                            await member.remove_roles(role)

                    region_role_id = self.region_role_ids[region]

                    # Fetch the relevant region role from the user's region
                    region_role = ctx.guild.get_role(region_role_id)

                    # Add the region role to the user
                    await member.add_roles(region_role)

            # noinspection PyUnresolvedReferences
            # Fetch the user's game stats for CSGO (app ID 730)
            game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

            game_stats = game_stats["playerstats"]["stats"]

            hours = 0

            # Calculate the playtime of the user in hours
            for game_stat in game_stats:
                if game_stat["name"] == 'total_time_played':
                    hours = round(game_stat["value"] / 3600)

            # Update the user's total playtime in the database
            update_hours(member.id, hours)

            await log_message(ctx, f'`{ctx.user}` has requested a stats update for `{member}`.')

            return await ctx.edit_original_message(content=messages["stats_updated"])


async def setup(bot):
    await bot.add_cog(Statistics(bot))
