import json
import string
import random
from io import BytesIO

import aiohttp
import requests
from steam.webapi import WebAPI
from PIL import Image, ImageFont, ImageDraw

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

from utils.db import already_exists, get_steam_id, get_country, get_bio, get_hours
from utils.tools import split_string

with open('config.json') as _json_file:
    _data = json.load(_json_file)
    whitelist = _data['whitelist']
    steam_key = _data['steam_key']


class LFG(ui.Modal, title='LFG Form'):
    age = ui.TextInput(label='Age', placeholder='Your age', required=False)
    role = ui.TextInput(label='Role', placeholder='Your role in a match')
    game_type = ui.TextInput(label='Game Type', placeholder='MM / FaceIT / Wingman / 1v1 / DZ')

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)

        try:
            _age = int(self.age.value)

        except ValueError:
            await ctx.edit_original_message(content='The age entered is invalid.')

        if self.game_type.value.lower() not in ['mm', 'faceit', 'wingman', '1v1', 'dz']:
            await ctx.edit_original_message(content='The game type entered is invalid.')


class LFP(ui.Modal, title='LFP Form'):
    name = ui.TextInput(label='Team Name', placeholder='The name of the team')
    country_region = ui.TextInput(label='Country / Region',
                                  placeholder='Which country / region should players be from?')
    requirements = ui.TextInput(label='Requirements',
                                placeholder='What expectations should the players fulfil? (Rank, Language, etc.)',
                                style=discord.TextStyle.paragraph)
    offers = ui.TextInput(label='Offers',
                          placeholder='What does the team offer to players?',
                          style=discord.TextStyle.paragraph)
    contact = ui.TextInput(label='Contact', placeholder='Whom/Where to contact for applying?')

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)


class LFT(ui.Modal, title='LFT Form'):
    age = ui.TextInput(label='Age', placeholder='Your age')
    role = ui.TextInput(label='Role', placeholder='Your role in a match')
    about_me = ui.TextInput(label='About Me', placeholder='A bit about yourself...', style=discord.TextStyle.paragraph)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)

        try:
            _age = int(self.age.value)

        except ValueError:
            await ctx.edit_original_message(content='The age entered is invalid.')


class LFC(ui.Modal, title='LFC Form'):
    name = ui.TextInput(label='Team Name', placeholder='The name of the team')
    country_region = ui.TextInput(label='Country / Region',
                                  placeholder='Which country / region should the coach be from?')
    experience = ui.TextInput(label='Experience', placeholder='How experienced coaches are you looking for?',
                              required=False)
    offers = ui.TextInput(label='Offers',
                                placeholder='What benefits would you offer to the coach?',
                                style=discord.TextStyle.paragraph)
    expectations = ui.TextInput(label='Expectations',
                                placeholder='What do you expect from the coach?',
                                style=discord.TextStyle.paragraph)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)


class LookingFor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.steamAPI = WebAPI(steam_key)

        with open('config.json') as json_file:
            data = json.load(json_file)
            self.lfg_channel_id = data['lfg_channel_id']
            self.lfp_channel_id = data['lfp_channel_id']
            self.lft_channel_id = data['lft_channel_id']
            self.lfc_channel_id = data['lfc_channel_id']

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

    @app_commands.command(name='lfg', description='Send a looking-for-game advertisement.')
    @app_commands.guilds(whitelist)
    async def _lfg(self, ctx: discord.Interaction):
        if not already_exists(ctx.user.id):
            return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet '
                                                           '(use `/link`).')

        modal = LFG()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        embed = discord.Embed(colour=self.bot.embed_colour)

        if modal.game_type.value.lower() == '1v1':
            embed.title = 'Looking for Game (1v1)'

        elif modal.game_type.value.lower() == 'wingman':
            embed.title = 'Looking for Game (Wingman)'

        elif modal.game_type.value.lower() == 'mm':
            embed.title = 'Looking for Game (Matchmaking)'

        elif modal.game_type.value.lower() == 'dz':
            embed.title = 'Looking for Game (Danger Zone)'

        elif modal.game_type.value.lower() == 'faceit':
            embed.title = 'Looking for Game (FaceIT)'

        steam_id = get_steam_id(ctx.user.id)

        async with aiohttp.ClientSession() as session:
            if modal.game_type.value.lower() != 'faceit':
                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" in stats.keys():
                        return await ctx.edit_original_message(content='No matchmaking stats found for this user.')

            else:
                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" in stats.keys():
                        return await ctx.edit_original_message(content='No FaceIT stats found for this user.')

        # noinspection PyUnresolvedReferences
        steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        hours = get_hours(ctx.user.id)

        embed.add_field(name='Player',
                        value=f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id})')

        embed.add_field(name='Age', value=modal.age.value)
        embed.add_field(name='Role', value=modal.role.value)
        embed.add_field(name='Hours', value=hours if hours else 'Private')

        if modal.game_type.value.lower() != 'faceit':
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

            country = get_country(ctx.user.id)

            if country:
                country_code = requests.get(f'https://restcountries.com/v3.1/name/{get_country(ctx.user.id)}') \
                    .json()[0]["cca2"].lower()

                response = requests.get(f'https://flagcdn.com/32x24/{country_code}.png')
                flag = Image.open(BytesIO(response.content))
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

            __bio = get_bio(ctx.user.id)

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

            file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

            buffer = BytesIO()
            _new.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename=f'{file_name}.png')

            embed.set_image(url=f'attachment://{file_name}.png')

        else:
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

            country = get_country(ctx.user.id)

            if country:
                country_code = requests.get(f'https://restcountries.com/v3.1/name/{get_country(ctx.user.id)}') \
                    .json()[0]["cca2"].lower()

                response = requests.get(f'https://flagcdn.com/32x24/{country_code}.png')
                flag = Image.open(BytesIO(response.content))
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

            __bio = get_bio(ctx.user.id)

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

            file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

            buffer = BytesIO()
            _new.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename=f'{file_name}.png')

            embed.set_image(url=f'attachment://{file_name}.png')

        channel = ctx.guild.get_channel(self.lfg_channel_id)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label='Message Me',
                              url=f'https://discord.com/users/{ctx.user.id}')
        )

        await channel.send(embed=embed, file=file, view=view)

        await ctx.edit_original_message(content=f'Your advertisement has been posted in {channel.mention}.')

    @app_commands.command(name='lfp', description='Send a looking-for-player advertisement.')
    @app_commands.guilds(whitelist)
    async def _lfp(self, ctx: discord.Interaction):
        modal = LFP()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Looking for Players'
        embed.description = f'**{modal.name.value}** is looking for players!'

        embed.add_field(name='Country / Region', value=modal.country_region.value)
        embed.add_field(name='Requirements', value=modal.requirements.value, inline=False)
        embed.add_field(name='Offers', value=modal.offers.value, inline=False)
        embed.add_field(name='Contact', value=modal.contact.value)

        channel = ctx.guild.get_channel(self.lfp_channel_id)

        await channel.send(embed=embed)

        await ctx.edit_original_message(content=f'Your advertisement has been posted in {channel.mention}.')

    @app_commands.command(name='lft', description='Send a looking-for-team advertisement.')
    @app_commands.guilds(whitelist)
    async def _lft(self, ctx: discord.Interaction):
        if not already_exists(ctx.user.id):
            return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet '
                                                           '(use `/link`).')

        modal = LFT()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        steam_id = get_steam_id(ctx.user.id)

        # noinspection PyUnresolvedReferences
        steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        hours = get_hours(ctx.user.id)

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Looking for Team'
        embed.description = f'**[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id})** ' \
                            f'is looking for a team!' \
                            f'\n\nUse `/mmstats` and `/faceitstats` to view their in-game statistics.'

        embed.add_field(name='Age', value=modal.age.value)
        embed.add_field(name='Role', value=modal.role.value)

        country = get_country(ctx.user.id)

        res = requests.get(f'https://restcountries.com/v3.1/name/{country}')

        res = res.json()

        region = res[0]["region"]

        if region == "Americas":
            region = res[0]["subregion"]

        embed.add_field(name='Country - Region', value=f'{country} - {region}')
        embed.add_field(name='Hours', value=hours if hours else 'Private')
        embed.add_field(name='About me', value=modal.about_me.value, inline=False)

        channel = ctx.guild.get_channel(self.lft_channel_id)

        await channel.send(embed=embed)

        await ctx.edit_original_message(content=f'Your advertisement has been posted in {channel.mention}.')

    @app_commands.command(name='lfc', description='Send a looking-for-coach advertisement.')
    @app_commands.guilds(whitelist)
    async def _lfc(self, ctx: discord.Interaction):
        modal = LFC()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.title = 'Looking for Coach'
        embed.description = f'**{modal.name.value}** are looking for a coach!'

        embed.add_field(name='Country / Region', value=modal.country_region.value)

        if modal.experience.value:
            embed.add_field(name='Experience', value=modal.experience.value)

        embed.add_field(name='Offers', value=modal.offers.value, inline=False)
        embed.add_field(name='Expectations', value=modal.expectations.value, inline=False)

        channel = ctx.guild.get_channel(self.lfc_channel_id)

        await channel.send(embed=embed)

        await ctx.edit_original_message(content=f'Your advertisement has been posted in {channel.mention}.')


async def setup(bot):
    await bot.add_cog(LookingFor(bot))
