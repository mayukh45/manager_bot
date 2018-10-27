import asyncio
import os
import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from mongodb_connector import MongoDBConnector
from checks import is_int

desc = 'A bot made by Mayukh to manage expenses'

db_name = 'manager_db'
loop = asyncio.get_event_loop()
db_connector = MongoDBConnector(os.getenv('MONGODB_SRV'), db_name='manager_db', loop=loop)
bot = Bot(command_prefix=commands.when_mentioned_or("!"), description=desc, loop=loop)


def not_expense(channel):
    return type(channel) is discord.channel.DMChannel or channel.name != "expenses"


def get_amount(message):
    for tokens in message.split(" "):
        if is_int(tokens):
            return int(tokens)


@bot.event
async def on_raw_reaction_add(payload):
    print("LOLWA")
    if str(payload.emoji) == "👌🏽":
        print("damn")


@bot.command()
async def paid(ctx):
    if not not_expense(ctx.message.channel):
        mentions = ctx.message.mentions
        IDs = [member.id for member in mentions]
        amount = get_amount(ctx.message.content)
        await db_connector.update(IDs, amount)


bot.run(os.getenv('TOKEN'))
