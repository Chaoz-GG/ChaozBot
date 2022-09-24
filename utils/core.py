import os


# Load all the cog classes from the `cogs` folder
async def load_cogs(bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
