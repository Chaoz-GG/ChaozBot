#!/usr/bin/python3

import discord
from discord.ext import commands

import json

from utils.tools import reply_message

from includes.errors import CustomError


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as f:
            data = json.load(f)

        self.prefix = data["prefix"]

    @commands.command(name='help')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _help(self, ctx, term: str = None):
        embed = discord.Embed(colour=self.bot.embed_colour)

        if term is None:
            embed.title = 'Commands'

            if ctx.guild is not None:
                embed.description = 'Here\'s a list of commands you can use. \nUse `$help <command>` for extended ' \
                                    'information on a command.' + f'\n\n**Command prefix:** `{self.prefix}`\n'

            else:
                embed.description = 'Here\'s a list of commands you can use. \nUse `$help <command>` for extended ' \
                                    'information on a command.' + f'\n\n**Command prefix:** `{self.prefix}`\n'

            embed.add_field(name='General',
                            value=f'`ping`',
                            inline=False)

            embed.add_field(name='Profile',
                            value=f'`steam`, `link`, `unlink`, `bio`, `country`',
                            inline=False)

            embed.add_field(name='Statistics',
                            value=f'`mmstats`, `faceitstats`, `update`',
                            inline=False)

            await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji1)

        else:
            term = term.lower()

            embed.description = '`<>` means required | `[]` means optional'

            if term == 'help':
                embed.title = 'Help Command'
                embed.add_field(name='Description',
                                value=f'You really need help with the "help" command?',
                                inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}help [command]`')

            # GENERAL

            elif term == 'ping':

                embed.title = 'Ping'
                embed.add_field(name='Description',
                                value='Returns the API and bot latency.',
                                inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}ping`')

            # UTILITY

            elif term == 'steam':
                embed.title = 'Steam User Profile'
                embed.add_field(name='Description',
                                value='Shows the profile of a steam user.', inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}steam <community_id/url>`')

            elif term == 'link':
                embed.title = 'Link Steam Profile'
                embed.add_field(name='Description',
                                value='Links your Steam profile with the bot.', inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}link <community_id/url>`')

            elif term == 'unlink':
                embed.title = 'Unlink Steam Profile'
                embed.add_field(name='Description',
                                value='De-links your Steam profile from the bot.', inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}unlink`')

            elif term == 'bio':
                embed.title = 'Set Bio'
                embed.add_field(name='Description',
                                value='Sets your bio.', inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}bio <text>`')

            elif term == 'country':
                embed.title = 'Set Country'
                embed.add_field(name='Description',
                                value='Sets your country.', inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}country <country_name>`')

            # FUN

            elif term == 'mmstats':
                embed.title = 'CSGO Matchmaking Statistics'
                embed.add_field(name='Description',
                                value='Shows the matchmaking statistics of the author / the mentioned user.',
                                inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}mmstats [user]`')

            elif term == 'faceitstats':
                embed.title = 'CSGO FaceIT Statistics'
                embed.add_field(name='Description',
                                value='Shows the FaceIT statistics of the author / the mentioned user.',
                                inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}faceitstats [user]`')

            elif term == 'update':
                embed.title = 'Update CSGO Statistics'
                embed.add_field(name='Description',
                                value='Updates the CSGO Matchmaking / FaceIT statistics of the author / '
                                      'the mentioned user, if available. **Can be used once every 30 minutes.**',
                                inline=False)
                embed.add_field(name='Usage', value=f'`{self.prefix}update [user]`')

            else:
                raise CustomError('No such command! '
                                  f'Use `{self.prefix}help` for a list of available commands.')

            await reply_message(ctx=ctx, embed=embed, emoji=self.bot.emoji1)


def setup(bot):
    bot.add_cog(Help(bot))
