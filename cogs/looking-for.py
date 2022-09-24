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

from utils.db import already_exists, get_steam_id, get_user, get_country, get_region, get_bio, get_hours, \
    get_team_by_id, get_teams_by_captain_id
from utils.tools import split_string, log_message, calculate_age

with open('config.json') as _json_file:
    _data = json.load(_json_file)
    whitelist = _data['whitelist']
    steam_key = _data['steam_key']

    lf_channel_id = _data['lf_channel_id']

    chaoz_text = _data['chaoz_text']
    chaoz_logo_url = _data['chaoz_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["looking-for"]


class LFG(ui.Modal, title='Looking For Game'):
    role = ui.TextInput(label='Role', placeholder='Your role in a match')
    game_type = ui.TextInput(label='Game Type', placeholder='MM / FaceIT / Wingman / 1v1 / DZ')

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)

        # Check if the game type entered is one of the valid types
        if self.game_type.value.lower() not in ['mm', 'faceit', 'wingman', '1v1', 'dz']:
            await ctx.edit_original_message(content=messages["invalid_game_type"])


class LFPTeamSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        modal = LFP()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        team = get_team_by_id(self.values[0])

        embed = discord.Embed(colour=0xffffff)

        embed.set_thumbnail(url=chaoz_logo_url)

        embed.title = 'Looking for Players'
        embed.description = f'**{team["name"]}** is looking for players!'

        embed.add_field(name='Region', value=team["region"])
        embed.add_field(name='Requirements', value=modal.requirements.value, inline=False)
        embed.add_field(name='Offers', value=modal.offers.value, inline=False)
        embed.add_field(name='Contact', value=ctx.guild.get_member(team["captain_discord_id"]).mention)

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in games.items():
            # Compare the active game of the team against the values in our games.json file
            if _game[1][0] == team['active_game']:
                embed.set_footer(text=team['active_game'], icon_url=f'https://bot.chaoz.gg/games/{_game[0]}.png')

        channel = ctx.guild.get_channel(lf_channel_id)

        await channel.send(embed=embed)

        await self.ctx.edit_original_message(content=messages["ad_posted"].format(channel.mention),
                                             embed=None, view=None)


class LFCTeamSelect(discord.ui.Select):
    def __init__(self, options):
        self.ctx = None

        super().__init__(placeholder='Select the team.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, ctx: discord.Interaction):
        modal = LFC()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        team = get_team_by_id(self.values[0])

        embed = discord.Embed(colour=0xffffff)

        embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)
        embed.set_thumbnail(url=f'https://bot.chaoz.gg/teams/{self.values[0]}.png')

        embed.title = 'Looking for Coach'
        embed.description = f'**{team["name"]}** are looking for a coach!'

        embed.add_field(name='Region', value=team["region"])

        if modal.experience.value:
            embed.add_field(name='Experience', value=modal.experience.value)

        embed.add_field(name='Offers', value=modal.offers.value, inline=False)
        embed.add_field(name='Expectations', value=modal.expectations.value, inline=False)
        embed.add_field(name='Contact', value=ctx.guild.get_member(team["captain_discord_id"]).mention)

        with open('data/games.json') as f:
            games = json.load(f)

        for _game in games.items():
            # Compare the active game of the team against the values in our games.json file
            if _game[1][0] == team['active_game']:
                embed.set_footer(text=team['active_game'], icon_url=f'https://bot.chaoz.gg/games/{_game[0]}.png')

        channel = ctx.guild.get_channel(lf_channel_id)

        await channel.send(embed=embed)

        await self.ctx.edit_original_message(content=messages["ad_posted"].format(channel.mention),
                                             embed=None, view=None)


class LFP(ui.Modal, title='Looking For Players'):
    requirements = ui.TextInput(label='Requirements',
                                placeholder='What expectations should the players fulfil? (Rank, Language, etc.)',
                                style=discord.TextStyle.paragraph)
    offers = ui.TextInput(label='Offers',
                          placeholder='What does the team offer to players?',
                          style=discord.TextStyle.paragraph)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)


class LFT(ui.Modal, title='Looking For Team'):
    role = ui.TextInput(label='Role', placeholder='Your role in a match')
    about_me = ui.TextInput(label='About Me', placeholder='A bit about yourself...', style=discord.TextStyle.paragraph)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)


class LFC(ui.Modal, title='Looking For Coach'):
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

        await ctx.response.defer()


class LookingFor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create a Steam WebAPI instance
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

        self.stats_text_color = '#ffffff'
        self.font = 'assets/fonts/arial.ttf'
        self.title_font = 'assets/fonts/Audiowide.ttf'
        self.bio_font = 'assets/fonts/DejaVuSans.ttf'

    @app_commands.command(name='lfg', description='Send a looking-for-game advertisement.')
    @app_commands.guilds(whitelist)
    async def _lfg(self, ctx: discord.Interaction):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Check if the user has already linked his profile
        if not already_exists(ctx.user.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        modal = LFG()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)

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
                # Fetch the matchmaking stats of the user
                async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                    stats = await stats.json()

                    if "error" in stats.keys():
                        return await ctx.edit_original_message(content=messages["mm_stats_not_found"])

            else:
                async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                    # Fetch the FaceIT stats of the user, if exists
                    stats = await stats.json()

                    if "error" in stats.keys():
                        return await ctx.edit_original_message(content=messages["faceit_stats_not_found"])

        # Fetch the user's Steam profile instance
        # noinspection PyUnresolvedReferences
        steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        user = get_user(ctx.user.id)
        hours = get_hours(ctx.user.id)

        embed.set_thumbnail(url=steam_user["avatarfull"])

        embed.description = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) - ' \
                            f'{ctx.user.mention} is looking for a **{modal.game_type.value}** game.'

        embed.add_field(name='Age', value=calculate_age(user["birthday"]))
        embed.add_field(name='Role', value=modal.role.value)
        embed.add_field(name='Hours', value=hours if hours else 'Private')

        if modal.game_type.value.lower() != 'faceit':
            # Open the image base from local assets
            base = Image.open('assets/images/profile-base.png')
            base = base.convert('RGB')

            _new = base.copy()

            new = ImageDraw.Draw(_new)

            mm_rank = list(self.mm_ranks.keys())[list(self.mm_ranks.values()).index(stats["rank"])]

            # Obtain the rank image of the user and paste on the base
            mm_rank_image = Image.open(f'assets/images/ranks/matchmaking/{mm_rank}.png')
            _new.paste(mm_rank_image, (85, 165))

            # Fetch the user's Steam avatar
            response = requests.get(f'{steam_user["avatarfull"]}')
            # Create a circular mask for the avatar
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

                # Fetch the country flag image
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

            # Create a buffer to convert it into the Discord file object
            buffer = BytesIO()
            _new.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(buffer, filename=f'{file_name}.png')

            embed.set_image(url=f'attachment://{file_name}.png')

        else:
            # Open the image base from local assets
            base = Image.open('assets/images/profile-base.png')
            base = base.convert('RGB')

            _new = base.copy()

            new = ImageDraw.Draw(_new)

            # Fetch the user's FaceIT rank image
            faceit_rank_image = Image.open(f'assets/images/ranks/faceit/{stats["rank"]}.png')

            faceit_rank_image = faceit_rank_image.convert("RGBA")
            big_size = (faceit_rank_image.size[0] * 3, faceit_rank_image.size[1] * 3)
            # Create circular mask for the FaceIT rank image
            mask = Image.new('L', big_size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + big_size, fill=255)
            mask = mask.resize(faceit_rank_image.size, Image.ANTIALIAS)
            faceit_rank_image.putalpha(mask)

            _new.paste(faceit_rank_image, (135, 165), faceit_rank_image)

            # Fetch the user's Steam avatar
            response = requests.get(f'{steam_user["avatarfull"]}')
            im = Image.open(BytesIO(response.content))
            im = im.convert("RGBA")
            im = im.resize((200, 200))
            big_size = (im.size[0] * 3, im.size[1] * 3)
            # Create circular mask for the Steam avatar
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

                # Fetch the country flag image
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

            # Create a buffer to convert it into the Discord file object
            buffer = BytesIO()
            _new.save(buffer, format="PNG")
            buffer.seek(0)

            # Create the Discord file object from buffer
            file = discord.File(buffer, filename=f'{file_name}.png')

            embed.set_image(url=f'attachment://{file_name}.png')

        channel = ctx.guild.get_channel(lf_channel_id)

        await channel.send(embed=embed, file=file)

        await ctx.edit_original_message(content=messages["ad_posted"].format(channel.mention))

    @app_commands.command(name='lfp', description='Send a looking-for-player advertisement.')
    @app_commands.guilds(whitelist)
    async def _lfp(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Fetch all the teams for which the user is a captain
        teams = get_teams_by_captain_id(ctx.user.id)

        if not teams:
            return await ctx.edit_original_message(content=messages["no_captain"])

        embed = discord.Embed(colour=0xffffff)

        embed.title = 'Select Team'
        embed.description = 'Which team would you like to post an advertisement for?\n'

        # Create the select options list for the fetched teams
        options = list()

        for i, team_details in enumerate(teams, 1):
            embed.description += f'\n`{i}.` {team_details[1]}'

            options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

        item = LFPTeamSelect(options=options)
        item.ctx = ctx

        view = discord.ui.View()
        view.add_item(item)

        await ctx.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='lft', description='Send a looking-for-team advertisement.')
    @app_commands.guilds(whitelist)
    async def _lft(self, ctx: discord.Interaction):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Check if the user has linked his profile with the bot first
        if not already_exists(ctx.user.id):
            return await ctx.edit_original_message(content=messages["profile_not_linked"])

        modal = LFT()
        await ctx.response.send_modal(modal)
        await modal.wait()

        ctx = modal.interaction

        steam_id = get_steam_id(ctx.user.id)
        # Fetch the Steam profile instance for the user
        # noinspection PyUnresolvedReferences
        steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        embed = discord.Embed(colour=self.bot.embed_colour)

        embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)
        embed.set_thumbnail(url=steam_user["avatarfull"])

        embed.title = 'Looking for Team'
        embed.description = f'**[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id})** ' \
                            f'- {ctx.user.mention} is looking for a team!' \
                            f'\n\nUse `/mmstats` and `/faceitstats` to view their in-game statistics.'

        user = get_user(ctx.user.id)

        embed.add_field(name='Age', value=calculate_age(user['birthday']))
        embed.add_field(name='Role', value=modal.role.value)

        country = get_country(ctx.user.id)
        region = get_region(ctx.user.id)
        hours = get_hours(ctx.user.id)

        embed.add_field(name='Country / Region', value=f'{country} / {region}')
        embed.add_field(name='Hours', value=hours if hours else 'Private')
        embed.add_field(name='About Me', value=modal.about_me.value, inline=False)

        channel = ctx.guild.get_channel(lf_channel_id)

        await channel.send(embed=embed)

        await ctx.edit_original_message(content=messages["ad_posted"].format(channel.mention))

    @app_commands.command(name='lfc', description='Send a looking-for-coach advertisement.')
    @app_commands.choices(seeker=[
        app_commands.Choice(name='Individual', value='individual'),
        app_commands.Choice(name='Team', value='team')
    ])
    @app_commands.guilds(whitelist)
    async def _lfc(self, ctx: discord.Interaction, seeker: app_commands.Choice[str]):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Check if the user seeking a coach is an individual or a team
        if seeker.value == 'individual':
            modal = LFC()
            await ctx.response.send_modal(modal)
            await modal.wait()

            ctx = modal.interaction

            embed = discord.Embed(colour=self.bot.embed_colour)

            steam_id = get_steam_id(ctx.user.id)
            # Fetch the Steam profile instance for the user
            # noinspection PyUnresolvedReferences
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            embed.set_author(name=chaoz_text, icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=steam_user["avatarfull"])

            embed.title = 'Looking for Coach'
            embed.description = f'[{steam_user["personaname"]}](https://steamcommunity.com/profiles/{steam_id}) ' \
                                f'- {ctx.user.mention} is looking for a coach!'

            country = get_country(ctx.user.id)
            region = get_region(ctx.user.id)

            embed.add_field(name='Country / Region', value=f'{country} / {region}')

            if modal.experience.value:
                embed.add_field(name='Experience', value=modal.experience.value)

            embed.add_field(name='Offers', value=modal.offers.value, inline=False)
            embed.add_field(name='Expectations', value=modal.expectations.value, inline=False)

            channel = ctx.guild.get_channel(lf_channel_id)

            await channel.send(embed=embed)

            await ctx.edit_original_message(content=messages["ad_posted"].format(channel.mention))

        else:
            await ctx.response.defer(thinking=True)

            # Fetch all the teams for which the user is a captain
            teams = get_teams_by_captain_id(ctx.user.id)

            if not teams:
                return await ctx.edit_original_message(content=messages["no_captain"])

            embed = discord.Embed(colour=0xffffff)

            embed.title = 'Select Team'
            embed.description = 'Which team would you like to post an advertisement for?\n'

            # Create the select options list for the teams that the user is a captain of
            options = list()

            for i, team_details in enumerate(teams, 1):
                embed.description += f'\n`{i}.` {team_details[1]}'

                options.append(discord.SelectOption(label=team_details[1], value=team_details[0]))

            item = LFCTeamSelect(options=options)
            item.ctx = ctx

            view = discord.ui.View()
            view.add_item(item)

            await ctx.edit_original_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(LookingFor(bot))
