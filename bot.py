#!/usr/bin/python3

import discord
from discord import app_commands
from discord.ext import tasks

import json
import math
import logging
import string
import random
from io import BytesIO
from datetime import datetime

import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID
from steam.enums import EPersonaState
from PIL import Image, ImageFont, ImageDraw


from utils.tools import make_list_embed, generate_token, split_string
from utils.db import get_steam_ids, get_steam_id, already_exists, remove_user, has_generated_token, initiate_auth, \
    cleanup_auth, get_token, add_user, get_bio, get_country, update_bio, update_country

with open('config.json') as json_file:
    data = json.load(json_file)
    token = data['bot_token']
    whitelist = data['whitelist']
    steam_key = data['steam_key']
    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']

logging.basicConfig(format='%(asctime)s - [%(levelname)s] %(message)s', level=logging.INFO)


# noinspection PyMethodMayBeStatic
class ChaozBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.getLogger('ChaozBot')


intents = discord.Intents.all()
bot = ChaozBot(intents=intents)
tree = app_commands.CommandTree(bot)

bot.launch_time = datetime.utcnow()
bot.steamAPI = WebAPI(steam_key)

bot.emoji1 = '\u2705'
bot.emoji2 = '\u274C'

bot.embed_colour = 0xc29e29

bot.stats_text_color = '#ffffff'

bot.font = 'assets/fonts/arial.ttf'

bot.mm_ranks = {
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

bot.mm_rank_role_ids = mm_rank_role_ids
bot.faceit_rank_role_ids = faceit_rank_role_ids
bot.region_role_ids = region_role_ids


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=whitelist))


# Auto-update stats
@tasks.loop(hours=12)
async def _update_stats():
    for steam_id in get_steam_ids():
        requests.get(f'http://localhost:5000/stats/update/mm/{steam_id}')
        requests.get(f'http://localhost:5000/stats/update/faceit/{steam_id}')


# Leave unexpected servers
@bot.event
async def on_guild_join(guild):
    if guild.id not in whitelist:
        await guild.leave()


# Erase member data on leaving
@bot.event
async def on_member_remove(member):
    if already_exists(member.id):
        steam_id = get_steam_id(member.id)

        remove_user(member.id, steam_id)


@app_commands.command(name='ping', description='Returns the API and bot latency.')
async def _ping(ctx: discord.Interaction):
    await ctx.response.defer(thinking=True)

    embed = discord.Embed(colour=bot.embed_colour)
    embed.description = '**Pong!**'

    ms = bot.latency*1000

    embed.add_field(name='API latency (Heartbeat)', value=f'`{int(ms)} ms`')

    t1 = datetime.utcnow().strftime("%f")

    await ctx.edit_original_message(embed=embed)

    t2 = datetime.utcnow().strftime("%f")

    diff = int(math.fabs((int(t2) - int(t1))/1000))

    embed.add_field(name='Bot latency (Round-trip)', value=f'`{diff} ms`')

    await ctx.edit_original_message(embed=embed)


# noinspection PyShadowingBuiltins
@app_commands.command(name='help', description='Help command!')
async def _help(ctx: discord.Interaction):
    await ctx.response.defer(thinking=True)

    embed = discord.Embed(colour=bot.embed_colour)

    embed.title = 'Commands'

    embed.add_field(name='General',
                    value=f'`ping`',
                    inline=False)

    embed.add_field(name='Profile',
                    value=f'`steam`, `link`, `unlink`, `bio`, `country`',
                    inline=False)

    embed.add_field(name='Statistics',
                    value=f'`mmstats`, `faceitstats`, `update`',
                    inline=False)

    await ctx.edit_original_message(embed=embed)


@app_commands.command(name='steam', description='Shows various information about the profile of a steam user.')
async def _steam(ctx: discord.Interaction, community_id: str):
    await ctx.response.defer(thinking=True)

    try:
        # noinspection PyUnresolvedReferences
        steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                    if 'https://steamcommunity.com/id/' not in community_id else community_id)

        if steam_id is None:
            steam_id = community_id

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

    except (requests.HTTPError, requests.exceptions.HTTPError, IndexError):
        message = 'No such user found ... make sure you are using a valid Steam community ID/URL!'
        return await ctx.edit_original_message(content=message)

    # noinspection PyUnresolvedReferences
    bans = bot.steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steam_id)["players"][0]

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
        embed.colour = bot.embed_colour
        embed.url = steam_user["profileurl"]
        embed.set_thumbnail(url=steam_user["avatarfull"])

        return await ctx.edit_original_message(embed=embed)

    # noinspection PyUnresolvedReferences
    group_count = len(bot.steamAPI.ISteamUser.GetUserGroupList_v1(steamid=steam_id)["response"]["groups"])

    games = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        "?key={}&steamid={}&include_played_free_games=1%format=json".format(
            steam_key, steam_id)).json()["response"]

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
    embed.colour = bot.embed_colour
    embed.url = steam_user["profileurl"]
    embed.set_thumbnail(url=steam_user["avatarfull"])

    await ctx.edit_original_message(embed=embed)


@app_commands.command(name='link', description='Links your Steam profile with the bot.')
async def _link(ctx: discord.Interaction, community_id: str):
    await ctx.response.defer(thinking=True, ephemeral=True)

    if not community_id:
        return await ctx.edit_original_message(content='Please provide your Steam community ID/URL.')

    if already_exists(ctx.user.id):
        return await ctx.edit_original_message(content='You have already linked your Steam profile, if you would like '
                                                       'to link a new Steam account, first use the `/unlink` command '
                                                       'and then link the new account.')

    try:
        # noinspection PyUnresolvedReferences
        steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                    if 'https://steamcommunity.com/id/' not in community_id else community_id)

        if steam_id is None:
            steam_id = community_id

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        if int(steam_user["steamid"]) in get_steam_ids():
            return await ctx.edit_original_message(content='This Steam account has already been linked '
                                                           'by another user.')

    except (requests.HTTPError, IndexError):
        message = 'No such user found ... make sure you are using a valid Steam community ID/URL!'
        return await ctx.edit_original_message(content=message)

    if not has_generated_token(ctx.user.id):
        _token = generate_token()
        initiate_auth(ctx.user.id, _token)

        return await ctx.edit_original_message(content=f'Please add `{_token}` to the end of your Steam profile name '
                                                       'and run this command again.')

    else:
        _token = get_token(ctx.user.id)

        if steam_user["personaname"].endswith(_token):
            add_user(ctx.user.id, steam_user["steamid"])
            cleanup_auth(ctx.user.id)

            if "loccountrycode" in steam_user.keys():
                res = requests.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}').json()
                update_country(ctx.user.id, res[0]["name"]["common"])

                region = res[0]["region"]

                if region == "Americas":
                    region = res[0]["subregion"]

                for role_id in bot.region_role_ids.values():
                    role = ctx.guild.get_role(role_id)

                    if role in ctx.user.roles:
                        await ctx.user.remove_roles(role)

                region_role_id = bot.region_role_ids[region]

                region_role = ctx.guild.get_role(region_role_id)

                await ctx.user.add_roles(region_role)

                return await ctx.edit_original_message(content='Verification successful! You may now remove the token '
                                                               'from your profile name on Steam.')

            else:
                return await ctx.edit_original_message(content='Verification successful! You may now remove the token '
                                                               'from your profile name on Steam.\n\n**NOTE:** '
                                                               'You do not have a country listed on your Steam profile.'
                                                               ' Please use the `/country` command to update it now.')

        else:
            return await ctx.edit_original_message(content=f'Verification token (`{_token}`) could not be detected, '
                                                           'please make sure the changes have been saved.')


@app_commands.command(name='unlink', description='De-links your Steam profile from the bot.')
async def _unlink(ctx: discord.Interaction):
    await ctx.response.defer(thinking=True)

    if already_exists(ctx.user.id):
        steam_id = get_steam_id(ctx.user.id)

        remove_user(ctx.user.id, steam_id)

        return await ctx.edit_original_message(content='Your Steam account has been unlinked.')

    else:
        return await ctx.edit_original_message(content='You have not linked your Steam account yet.')


@app_commands.command(name='bio', description='Sets your bio.')
async def _bio(ctx: discord.Interaction, *, bio: str):
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
async def _country(ctx: discord.Interaction, *, country: str):
    await ctx.response.defer(thinking=True)

    if already_exists(ctx.user.id):
        steam_id = get_steam_id(ctx.user.id)

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        if "loccountrycode" in steam_user.keys():
            return await ctx.edit_original_message(content='Only users without a country listed on their Steam profile '
                                                           'can use this command.')

        if len(country) > 25:
            return await ctx.edit_original_message(content='Country name cannot be more than 25 characters.')

        res = requests.get(f'https://restcountries.com/v3.1/name/{country}')

        if res.status_code == 404:
            return await ctx.edit_original_message(content='Invalid country name.')

        res = res.json()

        update_country(ctx.user.id, res[0]["name"]["common"])

        region = res[0]["region"]

        if region == "Americas":
            region = res[0]["subregion"]

        for role_id in bot.region_role_ids.values():
            role = ctx.guild.get_role(role_id)

            if role in ctx.user.roles:
                await ctx.user.remove_roles(role)

        region_role_id = bot.region_role_ids[region]

        region_role = ctx.guild.get_role(region_role_id)

        await ctx.user.add_roles(region_role)

        return await ctx.edit_original_message(content='Your country has been updated.')

    else:
        return await ctx.edit_original_message(content='You have not linked your Steam account yet.'
                                                       'Please do so first with the `$link steam_id` command.')


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


@app_commands.command(name='inv',
                      description='Calculates the inventory value of the author / the mentioned user, if found.')
async def _inv(ctx: discord.Interaction, member: discord.Member = None):
    await ctx.response.defer(thinking=True)

    if member is None:
        member = ctx.user

    if not already_exists(member.id):
        return await ctx.edit_original_message(content='This user hasn\'t linked their steam account yet.')

    else:
        steam_id = get_steam_id(member.id)

        inv = requests.get(f'http://localhost:5000/inventory/{steam_id}').json()

        if "error" in inv.keys():
            return await ctx.edit_original_message(content='No inventory details found for this user.')

        # noinspection PyUnresolvedReferences
        steam_user = bot.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        embed = discord.Embed(colour=bot.embed_colour)

        embed.title = steam_user["personaname"]
        embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

        embed.description = f'`{inv["item_count"]}` items worth `${inv["value"]}`.'

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label='View Inventory', url=f'https://steamcommunity.com/profiles/{steam_id}/inventory/')
        )

        await ctx.edit_original_message(embed=embed, view=view)


tree.add_command(_ping, guild=discord.Object(id=whitelist))
tree.add_command(_help, guild=discord.Object(id=whitelist))
tree.add_command(_steam, guild=discord.Object(id=whitelist))
tree.add_command(_link, guild=discord.Object(id=whitelist))
tree.add_command(_unlink, guild=discord.Object(id=whitelist))
tree.add_command(_bio, guild=discord.Object(id=whitelist))
tree.add_command(_country, guild=discord.Object(id=whitelist))
tree.add_command(_mm_stats, guild=discord.Object(id=whitelist))
tree.add_command(_faceit_stats, guild=discord.Object(id=whitelist))
tree.add_command(_update, guild=discord.Object(id=whitelist))
tree.add_command(_inv, guild=discord.Object(id=whitelist))

if __name__ == '__main__':
    bot.run(token)
