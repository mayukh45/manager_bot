import asyncio
import os
import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from mongodb_connector import MongoDBConnector
from checks import is_int

desc = 'A bot made by Mayukh to manage expenses, Interact with the bot only in the expenses channel'

db_name = 'manager_db'
loop = asyncio.get_event_loop()
db_connector = MongoDBConnector(os.getenv('MONGODB_SRV'), db_name='manager_db', loop=loop)
bot = Bot(command_prefix=commands.when_mentioned_or("!"), description=desc, loop=loop)


def is_DM(channel):
    """Returns True if the expenses channel is a DM channel"""
    return type(channel) is discord.channel.DMChannel


def get_amount(message):
    """Get the amount of money from a message"""
    for tokens in message.content.split(" "):
        if is_int(tokens):
            return int(tokens)


def fine_paid_message(message):
    return len(message.mentions) > 0 and get_amount(message) is not None and message.channel.name == "expenses"


@bot.event
async def on_guild_remove(guild):
    """Will remove this guilds Data from DB"""
    await db_connector.remove_guild(guild_id=guild.id)


@bot.event
async def on_guild_join(guild):
    """Add this guild in DB"""
    await db_connector.create_guild(name=guild.name, guild_id=guild.id)


@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)
    message = await channel.get_message(payload.message_id)
    mentions = message.mentions
    if not is_DM(channel) and user in mentions and str(payload.emoji) == "👍🏽" and fine_paid_message(message):
        pass


@bot.command()
async def paid(ctx):

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "expenses":
        message = ctx.message
        mentions = message.mentions
        await db_connector.pay(guild_id=message.guild.id, payee=message.author, paid_for=mentions, amount=get_amount(message), message=message)


@bot.command()
async def stats(ctx):
    """Shows the current stats of a member regarding his/her expenses"""
    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "stats":
        pass


@bot.command()
async def unverified(ctx):
    """Shows all the members unverified payments"""
    results = await db_connector.get_unverified(user=ctx.message.author, guild_id=ctx.message.guild.id)
    msg = ""

    for result in results:
        msg += result['message']+"\n"

    await ctx.send(msg)


bot.run(os.getenv('TOKEN'))
