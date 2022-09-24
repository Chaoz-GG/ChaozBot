import json
from datetime import datetime

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands, tasks

import aiohttp
import requests
from steam.webapi import WebAPI
from steam.steamid import SteamID
from steam.enums import EPersonaState

from utils.tools import make_list_embed, generate_token, log_message
from utils.db import get_steam_ids, get_steam_id, already_exists, remove_user, has_generated_token, initiate_auth, \
    cleanup_auth, get_token, add_user, update_birthday, update_timezone, update_bio, get_favorite_games, \
    update_favorite_games, update_country, update_region, update_hours, get_birthday_bois, get_user, \
    archive_exists, archive_user, unarchive_user


with open('config.json') as json_file:
    data = json.load(json_file)
    whitelist = data['whitelist']

    steam_key = data['steam_key']

    mm_rank_role_ids = data['mm_rank_role_ids']
    faceit_rank_role_ids = data['faceit_rank_role_ids']
    region_role_ids = data['region_role_ids']

    birthday_channel_id = data['birthday_channel_id']

    user_max_games = data['user_max_games']

    chaoz_logo_url = data['chaoz_logo_url']

with open('data/messages.json') as _json_file:
    messages = json.load(_json_file)
    messages = messages["profile"]


class ProfileForm(ui.Modal, title='Profile Update'):
    birthday = ui.TextInput(label='Birthday', placeholder='DD/MM/YYYY', max_length=10, required=False)
    timezone = ui.TextInput(label='Timezone', placeholder='Check https://bot.chaoz.gg/timezones.json', required=False)
    bio = ui.TextInput(label='Bio',
                       placeholder='Enter your bio ...',
                       style=discord.TextStyle.long,
                       max_length=300,
                       required=False)
    favorite_games = ui.Select(placeholder='Choose your favorite games ...', max_values=user_max_games, min_values=0)

    interaction: discord.Interaction = None

    async def on_submit(self, ctx: discord.Interaction):
        self.interaction = ctx

        await ctx.response.defer(thinking=True)

        with open('data/games.json') as f:
            games = json.load(f)

        # Create a list with all the available game role IDs
        game_role_ids = list()

        for game in games.values():
            game_role_ids.append(game[4])

        if self.birthday.value:
            # Get the birthday string in the correct format
            birthday = self.birthday.value.replace('/', '')

            # Create a datetime.date object from the birthday string
            try:
                birthday = datetime.strptime(birthday, "%d%m%Y").date()

            except ValueError:
                return await ctx.edit_original_response(content=messages["birthday_invalid"])

            # Update the user's birthday in the database
            update_birthday(ctx.user.id, birthday)

        if self.timezone.value:
            with open('data/timezones.json') as f:
                timezones = json.load(f)

            # Check if the timezone is valid
            if self.timezone.value not in timezones:
                return await ctx.edit_original_response(content=messages["timezone_invalid"])

            # Update the user's timezone in the database
            update_timezone(ctx.user.id, self.timezone.value)

        if self.bio.value:
            # Update the user's bio in the database
            update_bio(ctx.user.id, self.bio.value)

        if self.favorite_games.values:
            # Remove all the game role IDs from the user
            for role_id in game_role_ids:
                role = ctx.guild.get_role(role_id)

                if role in ctx.user.roles:
                    await ctx.user.remove_roles(role)

            _games = list()

            # Create a list with the selected games and add the selected game role IDs to the user
            for _game in self.favorite_games.values:
                _games.append(games[_game][0])

                game_role = ctx.guild.get_role(games[_game][4])
                await ctx.user.add_roles(game_role)

            # Update the user's favorite games in the database
            update_favorite_games(ctx.user.id, "|".join(_games))

        return await ctx.edit_original_response(content=messages["profile_updated"])


class UnlinkConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.ctx = None
        self.member = None

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u2714',
                       style=discord.ButtonStyle.green,
                       custom_id='persistent_view:delete_confirm')
    async def _confirm(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        steam_id = get_steam_id(self.member.id)

        # Remove the user from the database
        remove_user(self.member.id, steam_id)

        return await self.ctx.edit_original_response(content=messages["profile_unlink_success"], view=None)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='\u274C',
                       style=discord.ButtonStyle.red,
                       custom_id='persistent_view:delete_cancel')
    async def _cancel(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.defer()

        await self.ctx.edit_original_response(content=messages["action_cancel"], view=None)


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create a Steam WebAPI instance
        self.steamAPI = WebAPI(steam_key)

        self.mm_rank_role_ids = mm_rank_role_ids
        self.faceit_rank_role_ids = faceit_rank_role_ids
        self.region_role_ids = region_role_ids

    @app_commands.command(name='profile', description='Shows various information about the profile of a steam user.')
    @app_commands.guilds(whitelist)
    async def _profile(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # If no member was mentioned, use the author of the message
        if not member:
            member = ctx.user

        # Check if the user has linked their Steam profile with the bot first
        if not already_exists(member.id):
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

        steam_id = get_steam_id(member.id)

        # noinspection PyUnresolvedReferences
        # Fetch the user's profile data from the Steam WebAPI
        steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

        # noinspection PyUnresolvedReferences
        # Fetch the user's ban data from the Steam WebAPI
        bans = self.steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steam_id)["players"][0]

        ban_info = {"VAC Banned": bans["VACBanned"], "Community Banned": bans["CommunityBanned"]}

        if bans["VACBanned"]:
            ban_info["VAC Bans"] = bans["NumberOfVACBans"]
            ban_info["Days Since Last VAC Ban"] = bans["DaysSinceLastBan"]

        if steam_user["communityvisibilitystate"] != 3:
            embed = make_list_embed(ban_info, self.bot.embed_colour)

            embed.description = "This profile is private."
            embed.title = steam_user["personaname"]
            embed.colour = self.bot.embed_colour
            embed.url = steam_user["profileurl"]
            embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=steam_user["avatarfull"])

            return await ctx.edit_original_response(embed=embed)

        # noinspection PyUnresolvedReferences
        group_count = len(self.steamAPI.ISteamUser.GetUserGroupList_v1(steamid=steam_id)["response"]["groups"])

        async with aiohttp.ClientSession() as session:
            # Fetch the user's owned games data from the Steam WebAPI
            async with session.get("https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}"
                                   "&include_played_free_games=1%format=json".format(steam_key, steam_id)) as games:
                games = await games.json()
                games = games["response"]

            try:
                games_played = games["game_count"]

            except KeyError:
                games_played = 0

            state = EPersonaState(steam_user["personastate"]).name
            game_name = None

            if "gameid" in steam_user.keys():
                state = "In-game"
                game_id = steam_user["gameid"]
                # Fetch the game name from the Steam API using the app ID
                async with session.get("https://store.steampowered.com/api/appdetails?appids={}".format(game_id)) \
                        as game_name:
                    game_name = await game_name.json()
                    game_name = game_name[game_id]["data"]["name"]

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
        embed = make_list_embed(fields, self.bot.embed_colour)
        embed.title = steam_user["personaname"]
        embed.colour = self.bot.embed_colour
        embed.url = steam_user["profileurl"]
        embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
        embed.set_thumbnail(url=steam_user["avatarfull"])

        await ctx.edit_original_response(embed=embed)

    @app_commands.command(name='link', description='Links your Steam profile with the bot.')
    @app_commands.guilds(whitelist)
    async def _link(self, ctx: discord.Interaction, community_id: str):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Check if the user has already linked their Steam profile with the bot
        if already_exists(ctx.user.id):
            return await ctx.edit_original_response(content=messages["profile_previously_linked"])

        try:
            # noinspection PyUnresolvedReferences
            # Convert the entered Steam ID into the correct format for lookup
            steam_id = SteamID.from_url('https://steamcommunity.com/id/{}'.format(community_id)
                                        if 'https://steamcommunity.com/id/' not in community_id else community_id)

            if steam_id is None:
                steam_id = community_id

            # noinspection PyUnresolvedReferences
            # Fetch the user's profile data from the Steam WebAPI
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            steam_id = SteamID(steam_user["steamid"])

            if int(steam_user["steamid"]) in get_steam_ids():
                return await ctx.edit_original_response(content=messages["profile_already_linked"])

        except (requests.HTTPError, IndexError):
            return await ctx.edit_original_response(content=messages["profile_not_found"])

        # Check if the user has a generated verification token in the database
        if not has_generated_token(ctx.user.id):
            # Generate a verification token for th euser
            _token = generate_token()
            # Initiate the verification process
            initiate_auth(ctx.user.id, _token)

            return await ctx.edit_original_response(content=messages["auth_add_token"].format(_token))

        else:
            # Retrieve the user's verification token from the database
            _token = get_token(ctx.user.id)

            if steam_user["personaname"].endswith(_token):
                # Add the user to the database
                add_user(ctx.user.id, steam_user["steamid"])
                # Remove the user's verification token from the database
                cleanup_auth(ctx.user.id)

                await ctx.edit_original_response(content=messages["profile_link_success"])

                # noinspection PyUnresolvedReferences
                # Fetch the user's game stats for CSGO (app ID 730) from the Steam WebAPI
                game_stats = self.steamAPI.ISteamUserStats.GetUserStatsForGame_v2(steamid=steam_id, appid=730)

                game_stats = game_stats["playerstats"]["stats"]

                hours = 0

                for game_stat in game_stats:
                    if game_stat["name"] == 'total_time_played':
                        hours = round(game_stat["value"] / 3600)

                # Update the user's total playtime in the database
                update_hours(ctx.user.id, hours)

                async with aiohttp.ClientSession() as session:
                    # Fetch the user's matchmaking stats
                    async with session.get(f'http://localhost:5000/stats/view/mm/{steam_id}') as stats:
                        stats = await stats.json()

                    if "error" not in stats.keys():
                        # Remove all the matchmaking roles from the user
                        for role_id in self.mm_rank_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        # Fetch the matchmaking role from the user's matchmaking rank
                        rank_role = ctx.guild.get_role(self.mm_rank_role_ids[stats["rank"]])

                        # Add the matchmaking role to the user
                        await ctx.user.add_roles(rank_role)

                    # Fetch the user's FaceIT stats
                    async with session.get(f'http://localhost:5000/stats/view/faceit/{steam_id}') as stats:
                        stats = await stats.json()

                    if "error" not in stats.keys():
                        # Remove all the FaceIT roles from the user
                        for role_id in self.faceit_rank_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        # Fetch the FaceIT role from the user's FaceIT rank
                        rank_role = ctx.guild.get_role(self.faceit_rank_role_ids[str(stats["rank"])])

                        # Add the FaceIT role to the user
                        await ctx.user.add_roles(rank_role)

                    if "loccountrycode" in steam_user.keys():
                        # Fetch the user's country name from the Rest Countries API
                        async with session.get(f'https://restcountries.com/v3.1/alpha/{steam_user["loccountrycode"]}') \
                                as res:
                            res = await res.json()

                        # Update the user's country name in the database
                        update_country(ctx.user.id, res[0]["name"]["common"])

                        region = res[0]["region"]

                        if region == "Americas":
                            region = res[0]["subregion"]

                        # Update the user's region in the database
                        update_region(ctx.user.id, region)

                        # Remove all the region roles from the user
                        for role_id in self.region_role_ids.values():
                            role = ctx.guild.get_role(role_id)

                            if role in ctx.user.roles:
                                await ctx.user.remove_roles(role)

                        region_role_id = self.region_role_ids[region]

                        # Fetch the region role from the user's region
                        region_role = ctx.guild.get_role(region_role_id)

                        # Add the region role to the user
                        await ctx.user.add_roles(region_role)

                return await log_message(ctx, f'`{ctx.user}` have linked their Steam profile.')

            else:
                return await ctx.edit_original_response(content=messages["auth_token_undetected"].format(_token))

    @app_commands.command(name='unlink', description='De-links your Steam profile from the bot.')
    @app_commands.guilds(whitelist)
    async def _unlink(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True, ephemeral=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # Check if the user has a linked Steam profile in the database
        if already_exists(ctx.user.id):
            # Send a confirmation view for the unlink process to complete
            view = UnlinkConfirm()
            view.ctx = ctx
            view.member = ctx.user

            return await ctx.edit_original_response(content='Would you like to proceed?', view=view)

        else:
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

    @app_commands.command(name='setup', description='Setup your profile.')
    @app_commands.guilds(whitelist)
    async def _setup(self, ctx: discord.Interaction):
        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if not already_exists(ctx.user.id):
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

        # Create the profile setup form
        modal = ProfileForm()

        options = list()

        with open('data/games.json') as f:
            games = json.load(f)

        # Fetch the favorite games of the user from the database
        fav_games = get_favorite_games(ctx.user.id)

        # Create select options for the available games
        for abbr, game in games.items():
            if game[0] in fav_games:
                # Check the option for each favorite game
                options.append(discord.SelectOption(label=game[0], value=abbr, default=True))

            else:
                options.append(discord.SelectOption(label=game[0], value=abbr))

        modal.favorite_games.options = options

        await ctx.response.send_modal(modal)
        await modal.wait()

    @app_commands.command(name='country', description='Sets your country.')
    @app_commands.guilds(whitelist)
    async def _country(self, ctx: discord.Interaction, *, country: str):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        if already_exists(ctx.user.id):
            steam_id = get_steam_id(ctx.user.id)

            # noinspection PyUnresolvedReferences
            # Fetch the user's Steam profile from the Steam API
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            # This command is only for those users who do not have a country set on their Steam profile
            if "loccountrycode" in steam_user.keys():
                return await ctx.edit_original_response(content=messages["country_link_warning"])

            if len(country) > 25:
                return await ctx.edit_original_response(content=messages["country_too_long"])

            async with aiohttp.ClientSession() as session:
                # Check if the entered country name is valid using the Rest Countries API
                async with session.get(f'https://restcountries.com/v3.1/name/{country}') as res:
                    if res.status == 404:
                        return await ctx.edit_original_response(content='Invalid country name.')

                    res = await res.json()

            # Update the user's country name in the database
            update_country(ctx.user.id, res[0]["name"]["common"])

            region = res[0]["region"]

            if region == "Americas":
                region = res[0]["subregion"]

            # Update the user's region in the database
            update_region(ctx.user.id, region)

            # Remove all the region roles from the user
            for role_id in self.region_role_ids.values():
                role = ctx.guild.get_role(role_id)

                if role in ctx.user.roles:
                    await ctx.user.remove_roles(role)

            region_role_id = self.region_role_ids[region]

            # Fetch the region role from the user's region
            region_role = ctx.guild.get_role(region_role_id)

            # Add the region role to the user
            await ctx.user.add_roles(region_role)

            return await ctx.edit_original_response(content=messages["country_updated"])

        else:
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

    @app_commands.command(name='inv',
                          description='Calculates the inventory value of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _inv(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # If no member is mentioned, use the author of the message
        if member is None:
            member = ctx.user

        # Check if the user has a linked Steam profile in the database
        if not already_exists(member.id):
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

        else:
            steam_id = get_steam_id(member.id)

            async with aiohttp.ClientSession() as session:
                # Fetch the user's inventory information
                async with session.get(f'http://localhost:5000/inventory/{steam_id}') as inv:
                    inv = await inv.json()

            if "error" in inv.keys():
                return await ctx.edit_original_response(content=messages["inventory_error"])

            # noinspection PyUnresolvedReferences
            # Fetch the user's Steam profile from the Steam API
            steam_user = self.steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)["response"]["players"][0]

            embed = discord.Embed(colour=self.bot.embed_colour)

            embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=steam_user["avatarfull"])

            embed.title = steam_user["personaname"]
            embed.url = f'https://steamcommunity.com/profiles/{steam_id}'

            embed.description = f'`{inv["item_count"]}` items worth `${inv["value"]}`.'

            view = discord.ui.View()
            # Add a button to directly link to the user's Steam inventory
            view.add_item(
                discord.ui.Button(label='View Inventory',
                                  url=f'https://steamcommunity.com/profiles/{steam_id}/inventory/')
            )

            await ctx.edit_original_response(embed=embed, view=view)

    @app_commands.command(name='user',
                          description='Displays the profile of the author / the mentioned user, if found.')
    @app_commands.guilds(whitelist)
    async def _user(self, ctx: discord.Interaction, member: discord.Member = None):
        await ctx.response.defer(thinking=True)

        await log_message(ctx, f'`{ctx.user}` has used the `{ctx.command.name}` command.')

        # If no member is mentioned, use the author of the message
        if member is None:
            member = ctx.user

        # Check if the user has a linked Steam profile in the database
        if not already_exists(member.id):
            return await ctx.edit_original_response(content=messages["profile_not_linked"])

        else:
            user = get_user(member.id)

            embed = discord.Embed(colour=self.bot.embed_colour)

            embed.title = member.__str__()
            embed.description = user["bio"]

            embed.set_author(name='Chaoz Gaming', icon_url=chaoz_logo_url)
            embed.set_thumbnail(url=member.display_avatar.url)

            embed.add_field(name='Country', value=user["country"] or "Not set")
            embed.add_field(name='Region', value=user["region"] or "Not set")
            embed.add_field(name='Birthday', value=user["birthday"].strftime("%d %B, %Y")
                            if user["birthday"] else "Not set")
            embed.add_field(name='Timezone', value=user["timezone"])
            embed.add_field(name='Favorite Game', value=user["favorite_game"] or "Not set")

            embed.set_footer(text='Use `/profile` to update your profile information.')

            await ctx.edit_original_response(embed=embed)

    @tasks.loop(hours=24)
    async def wish_users(self):
        # Fetch the list of users whose birthdate is today
        users = get_birthday_bois()

        if not users:
            return

        birthday_channel = self.bot.get_channel(birthday_channel_id)

        for _user in users:
            # Get the user object from the user ID
            user = self.bot.get_user(_user[0])

            # If the user is not found, skip to the next entry
            if not user:
                continue

            # Try to send a DM to the user, and if it fails, just pass
            try:
                await user.send(messages["birthday_message"].format(user.mention))

            except (discord.Forbidden, discord.errors.Forbidden):
                pass

            # Send a message in the birthday channel
            await birthday_channel.send(messages["birthday_message"].format(user.mention))

    @wish_users.before_loop
    async def _before_wish_users(self):
        # Wait until the bot is ready before starting the task
        await self.bot.wait_until_ready()

    async def cog_load(self) -> None:
        # Start the task on cog load
        self.wish_users.start()

    async def cog_unload(self) -> None:
        # Cancel the task on cog unload
        self.wish_users.cancel()

    # Retrieve member data on joining, if exists
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Check if an archive entry for this user exists
        if archive_exists(member.id):
            # Retrieve the archive entry and push it into the active users
            unarchive_user(member.id)

    # Erase member data on leaving, if exists
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Check if the user exists in our database first
        if already_exists(member.id):
            steam_id = get_steam_id(member.id)

            # Archive the user data
            archive_user(member.id, steam_id)


async def setup(bot):
    await bot.add_cog(Profile(bot))
