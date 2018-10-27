import asyncio
import os
import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from mongodb_connector import MongoDBConnector

desc = 'A bot made by Mayukh to manage expenses'

db_name = 'manager_db'
loop = asyncio.get_event_loop()
db_connector = MongoDBConnector(os.getenv('MONGODB_SRV'), db_name='manager_db', loop=loop)
bot = Bot(command_prefix=commands.when_mentioned_or("!"), description=desc, loop=loop)

@bot.event
async def on_raw_reaction_add(payload):
    print("LOLWA")
    if str(payload.emoji) == "👌🏽":
        print("damn")


@bot.command()
async def paid(ctx,arg):
    print(ctx.message.content)

bot.run(os.getenv('TOKEN'))