#!/usr/bin/python3

import discord
from discord.ext import commands

import os
import json
import string
import random
from io import BytesIO


import requests
from steam.webapi import WebAPI
from PIL import Image, ImageFont, ImageDraw

from utils.tools import reply_message, reply_file, split_string
from utils.db import already_exists, get_steam_id, get_bio, get_country


class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.key = data['steam_key']

        self.steamAPI = WebAPI(self.key)

        self.stats_text_color = '#ffffff'
        
        self.font = ImageFont.load_default()

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

    @commands.command(name='mmstats')
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _mm_stats(self, ctx, member: discord.Member = None):

        if member is None:
            member = ctx.author

        if not already_exists(member.id):

            return await reply_message(ctx=ctx,
                                       content='This user hasn\'t linked their steam account yet.',
                                       emoji=self.bot.emoji2)

        else:
            async with ctx.typing():
                steam_id = get_steam_id(member.id)

                stats = requests.get(f'http://localhost:5000/stats/view/mm/{steam_id}').json()

                # noinspection PyUnresolvedReferences
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                embed = discord.Embed(colour=self.bot.embed_colour)

                embed.title = steam_user["personaname"]
                embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

                base = Image.open('assets/images/profile-base.png')
                base = base.convert('RGB')

                _new = base.copy()

                new = ImageDraw.Draw(_new)

                mm_rank = list(self.mm_ranks.keys())[list(self.mm_ranks.values()).index(stats["rank"])]

                mm_rank_image = Image.open(f'assets/images/ranks/matchmaking/{mm_rank}.png')
                _new.paste(mm_rank_image, (85, 165))

                response = requests.get(f'{steam_user["avatarfull"]}')
                im = Image.open(BytesIO(response.content))
                im = im.convert("RGBA")
                im = im.resize((200, 200))
                big_size = (im.size[0] * 3, im.size[1] * 3)
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(im.size, Image.ANTIALIAS)
                im.putalpha(mask)

                _new.paste(im, (836, 62), im)

                country = get_country(member.id)

                if country:
                    country_code = requests.get(f'https://restcountries.com/v3.1/name/{get_country(member.id)}') \
                        .json()[0]["cca2"].lower()

                    response = requests.get(f'https://flagcdn.com/32x24/{country_code}.png')
                    flag = Image.open(BytesIO(response.content))
                    flag = flag.convert("RGBA")

                    _new.paste(flag, (820, 370))

                else:
                    country = "Country not set."

                _country = f"""
                Country:       {country}
                """

                new.text((20, 20), f'{steam_user["personaname"]} ({steam_id})',
                         font=ImageFont.truetype('assets/fonts/DejaVuSans.ttf', 45))

                _two = f"""
                ADR: {stats["adr"]}
                """

                _three = f"""
                K/D: {stats["kpd"]}
                HLTV Rating: {stats["rating"]}
                Clutch%: {stats["clutch"]}
                """

                _four = f"""
                Best Weapon:
                {stats["best_weapon"]}
                """

                _five = f"""
                HS%: {stats["hs"]}
                
                Win Rate: {stats["win_rate"]}
                """

                _six = f"""
                Most Successful Map:
                {stats["most_successful_map"]}
                Most Played Map:
                {stats["most_played_map"]}
                """

                _bio = get_bio(member.id)

                if _bio:
                    _bio = split_string(text=_bio, limit=35)

                    _bio = '\n'.join(_bio)

                else:
                    _bio = "Bio not set."

                new.text((320, 155), _two, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((-75, 300), _three, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((250, 300), _four, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((-75, 500), _five, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((265, 500), _six, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)
                new.text((720, 410), _bio, font=ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 25),
                         fill=self.stats_text_color)
                new.text((605, 340), _country, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)

                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

                _new.save(f'temp/{file_name}.png')
                file = discord.File(f'temp/{file_name}.png', filename=f'{file_name}.png')

                embed.set_image(url=f'attachment://{file_name}.png')

                embed.set_footer(text='Stats are updated every 12 hours.')

                await reply_file(ctx=ctx,
                                 f=file,
                                 embed=embed,
                                 emoji=self.bot.emoji1)

                return os.remove(f'temp/{file_name}.png')

    @commands.command(name='faceitstats')
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _faceit_stats(self, ctx, member: discord.Member = None):

        if member is None:
            member = ctx.author

        if not already_exists(member.id):

            return await reply_message(ctx=ctx,
                                       content='This user hasn\'t linked their steam account yet.',
                                       emoji=self.bot.emoji2)

        else:
            async with ctx.typing():
                steam_id = get_steam_id(member.id)

                stats = requests.get(f'http://localhost:5000/stats/view/faceit/{steam_id}').json()

                if "error" in stats.keys():
                    return await reply_message(ctx=ctx,
                                               content='No FaceIT stats found for this user.',
                                               emoji=self.bot.emoji2)

                # noinspection PyUnresolvedReferences
                steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

                embed = discord.Embed(colour=self.bot.embed_colour)

                embed.title = steam_user["personaname"]
                embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

                base = Image.open('assets/images/profile-base.png')
                base = base.convert('RGB')

                _new = base.copy()

                new = ImageDraw.Draw(_new)

                faceit_rank_image = Image.open(f'assets/images/ranks/faceit/{stats["rank"]}.png')

                faceit_rank_image = faceit_rank_image.convert("RGBA")
                big_size = (faceit_rank_image.size[0] * 3, faceit_rank_image.size[1] * 3)
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(faceit_rank_image.size, Image.ANTIALIAS)
                faceit_rank_image.putalpha(mask)

                _new.paste(faceit_rank_image, (135, 165), faceit_rank_image)

                response = requests.get(f'{steam_user["avatarfull"]}')
                im = Image.open(BytesIO(response.content))
                im = im.convert("RGBA")
                im = im.resize((200, 200))
                big_size = (im.size[0] * 3, im.size[1] * 3)
                mask = Image.new('L', big_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + big_size, fill=255)
                mask = mask.resize(im.size, Image.ANTIALIAS)
                im.putalpha(mask)

                _new.paste(im, (836, 62), im)

                country = get_country(member.id)

                if country:
                    country_code = requests.get(f'https://restcountries.com/v3.1/name/{get_country(member.id)}') \
                        .json()[0]["cca2"].lower()

                    response = requests.get(f'https://flagcdn.com/32x24/{country_code}.png')
                    flag = Image.open(BytesIO(response.content))
                    flag = flag.convert("RGBA")

                    _new.paste(flag, (820, 370))

                else:
                    country = "Country not set."

                _country = f"""
                    Country:       {country}
                    """

                new.text((20, 20), f'{steam_user["personaname"]} ({steam_id})',
                         font=ImageFont.truetype('assets/fonts/DejaVuSans.ttf', 45))

                _two = f"""
                    ELO: {stats["elo"]}
                    """

                _three = f"""
                    K/D: {stats["kpd"]}
                    
                    HLTV Rating: {stats["rating"]}
                    """

                _four = f"""
                    Matches: {stats["matches"]}
                    """

                _five = f"""
                    HS%: {stats["hs"]}
                    
                    Win Rate: {stats["win_rate"]}
                    """

                _six = f"""
                    Most Successful Map:
                    {stats["most_successful_map"]}
                    Most Played Map:
                    {stats["most_played_map"]}
                    """

                _bio = get_bio(member.id)

                if _bio:
                    _bio = split_string(text=_bio, limit=35)

                    _bio = '\n'.join(_bio)

                else:
                    _bio = "Bio not set."

                new.text((280, 155), _two, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((-105, 300), _three, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((260, 350), _four, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((-105, 500), _five, font=ImageFont.truetype(self.font, 30), fill=self.stats_text_color)
                new.text((240, 500), _six, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)
                new.text((720, 410), _bio, font=ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 25),
                         fill=self.stats_text_color)
                new.text((575, 340), _country, font=ImageFont.truetype(self.font, 25), fill=self.stats_text_color)

                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

                _new.save(f'temp/{file_name}.png')
                file = discord.File(f'temp/{file_name}.png', filename=f'{file_name}.png')

                embed.set_image(url=f'attachment://{file_name}.png')

                embed.set_footer(text='Stats are updated every 12 hours.')

                await reply_file(ctx=ctx,
                                 f=file,
                                 embed=embed,
                                 emoji=self.bot.emoji1)

                return os.remove(f'temp/{file_name}.png')

    @commands.command(name='update')
    @commands.guild_only()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def _update(self, ctx):
        if not already_exists(ctx.author.id):

            return await reply_message(ctx=ctx,
                                       content='You have not linked your steam account yet.',
                                       emoji=self.bot.emoji2)

        else:
            async with ctx.typing():
                requests.get(f'http://localhost:5000/stats/update/mm/{get_steam_id(ctx.author.id)}',
                             timeout=30)

                requests.get(f'http://localhost:5000/stats/update/faceit/{get_steam_id(ctx.author.id)}',
                             timeout=30)

                return await reply_message(ctx=ctx,
                                           content='The stats have been updated.',
                                           emoji=self.bot.emoji1)


def setup(bot):
    bot.add_cog(Statistics(bot))
