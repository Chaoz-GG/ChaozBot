#!/usr/bin/python3

import discord
from discord import app_commands

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


@app_commands.command(name='mmstats',
                      description='Shows the matchmaking statistics of the author / the mentioned user, if found.')
async def _mm_stats(ctx: discord.Interaction, member: discord.Member = None):
    await ctx.response.defer(thinking=True)

    if member is None:
        member = ctx.user

    if not already_exists(member.id):

        return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet.')

    else:
        steam_id = get_steam_id(member.id)

        stats = requests.get(f'http://localhost:5000/stats/view/mm/{steam_id}').json()

        if "error" in stats.keys():
            return await ctx.edit_original_message(content='No matchmaking stats found for this user.')

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        embed = discord.Embed(colour=bot.embed_colour)

        embed.title = steam_user["personaname"]
        embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

        base = Image.open('assets/images/profile-base.png')
        base = base.convert('RGB')

        _new = base.copy()

        new = ImageDraw.Draw(_new)

        mm_rank = list(bot.mm_ranks.keys())[list(bot.mm_ranks.values()).index(stats["rank"])]

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

        __country = f"""Country:       {country}"""

        new.text((20, 20), 'Matchmaking Stats', font=ImageFont.truetype(bot.font, 45))

        _two = f"""ADR: {stats["adr"]}"""

        _three = f"""K/D: {stats["kpd"]}\nHLTV Rating: {stats["rating"]}\nClutch%: {stats["clutch"]}"""

        _four = f"""Best Weapon: {stats["best_weapon"]}"""

        _five = f"""HS%: {stats["hs"]}\nWin Rate: {stats["win_rate"]}"""

        _six = f"""Most Successful Map:\n{stats["most_successful_map"]}\nMost Played Map:\n{stats["most_played_map"]}"""

        __bio = get_bio(member.id)

        if __bio:
            __bio = split_string(text=__bio, limit=35)

            __bio = '\n'.join(__bio)

        else:
            __bio = "Bio not set."

        new.text((460, 185), _two, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((55, 330), _three, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((380, 330), _four, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((55, 530), _five, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((390, 530), _six, font=ImageFont.truetype(bot.font, 25), fill=bot.stats_text_color)
        new.text((720, 410), __bio, font=ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 25),
                 fill=bot.stats_text_color)
        new.text((720, 365), __country, font=ImageFont.truetype(bot.font, 25), fill=bot.stats_text_color)

        file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

        buffer = BytesIO()
        _new.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename=f'{file_name}.png')

        embed.set_image(url=f'attachment://{file_name}.png')

        embed.set_footer(text='Stats are updated every 12 hours.')

        for role_id in bot.mm_rank_role_ids.values():
            role = ctx.guild.get_role(role_id)

            if role in member.roles:
                await member.remove_roles(role)

        rank_role = ctx.guild.get_role(bot.mm_rank_role_ids[stats["rank"]])

        await member.add_roles(rank_role)

        await ctx.edit_original_message(attachments=[file], embed=embed)


@app_commands.command(name='faceitstats',
                      description='Shows the FaceIT statistics of the author / the mentioned user, if found.')
async def _faceit_stats(ctx: discord.Interaction, member: discord.Member = None):
    await ctx.response.defer(thinking=True)

    if member is None:
        member = ctx.user

    if not already_exists(member.id):

        return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet.')

    else:
        steam_id = get_steam_id(member.id)

        stats = requests.get(f'http://localhost:5000/stats/view/faceit/{steam_id}').json()

        if "error" in stats.keys():
            return await ctx.edit_original_message(content='No FaceIT stats found for this user.')

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        embed = discord.Embed(colour=bot.embed_colour)

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

        __country = f"""Country:       {country}"""

        new.text((20, 20), 'FaceIT Stats', font=ImageFont.truetype(bot.font, 45))

        _two = f"""ELO: {stats["elo"]}"""

        _three = f"""K/D: {stats["kpd"]}\n\nHLTV Rating: {stats["rating"]}"""

        _four = f"""Matches: {stats["matches"]}"""

        _five = f"""HS%: {stats["hs"]}\n\nWin Rate: {stats["win_rate"]}"""

        _six = f"""Most Successful Map:\n{stats["most_successful_map"]}\nMost Played Map:\n{stats["most_played_map"]}"""

        __bio = get_bio(member.id)

        if __bio:
            __bio = split_string(text=__bio, limit=35)

            __bio = '\n'.join(__bio)

        else:
            __bio = "Bio not set."

        new.text((450, 185), _two, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((55, 340), _three, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((420, 375), _four, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((55, 540), _five, font=ImageFont.truetype(bot.font, 30), fill=bot.stats_text_color)
        new.text((390, 530), _six, font=ImageFont.truetype(bot.font, 25), fill=bot.stats_text_color)
        new.text((720, 410), __bio, font=ImageFont.truetype("assets/fonts/DejaVuSans.ttf", 25),
                 fill=bot.stats_text_color)
        new.text((720, 365), __country, font=ImageFont.truetype(bot.font, 25), fill=bot.stats_text_color)

        file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

        buffer = BytesIO()
        _new.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename=f'{file_name}.png')

        embed.set_image(url=f'attachment://{file_name}.png')

        embed.set_footer(text='Stats are updated every 12 hours.')

        for role_id in bot.faceit_rank_role_ids.values():
            role = ctx.guild.get_role(role_id)

            if role in member.roles:
                await member.remove_roles(role)

        rank_role = ctx.guild.get_role(bot.faceit_rank_role_ids[str(stats["rank"])])

        await member.add_roles(rank_role)

        await ctx.edit_original_message(attachments=[file], embed=embed)


@app_commands.command(name='update',
                      description='Updates the CSGO Matchmaking / FaceIT statistics of the author, if available.')
async def _update(ctx: discord.Interaction):
    await ctx.response.defer(thinking=True)

    if not already_exists(ctx.user.id):

        return await ctx.edit_original_message(content='You have not linked your steam account yet.')

    else:

        requests.get(f'http://localhost:5000/stats/update/mm/{get_steam_id(ctx.user.id)}',
                     timeout=30)

        requests.get(f'http://localhost:5000/stats/update/faceit/{get_steam_id(ctx.user.id)}',
                     timeout=30)

        return await ctx.edit_original_message(content='The stats have been updated.')
