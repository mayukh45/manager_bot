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


def not_expense(channel):
    """Returns True if the parameter is not a expenses channel"""
    return type(channel) is discord.channel.DMChannel or channel.name != "expenses"


def get_amount(message):
    """Get the amount of money from a message"""
    for tokens in message.split(" "):
        if is_int(tokens):
            return int(tokens)


def fine_paid_message(message):
    return len(message.mentions) > 0 and get_amount(message.content) is not None


@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)
    message = await channel.get_message(payload.message_id)
    mentions = message.mentions
    if not not_expense(channel) and user in mentions and str(payload.emoji) == "👍🏽" and fine_paid_message(message):
        pass





@bot.command()
async def paid(ctx):

    if not not_expense(ctx.message.channel):
        # ADD message ID to db of the author of this command.

        mentions = ctx.message.mentions
        auth = ctx.message.author
        IDs = [member.id for member in mentions]
        amount = get_amount(ctx.message.content)
        for member in mentions:
            if member.dm_channel is None:
                await member.create_dm()
            message = "{0} paid {1} for you, If he/she really did, give a <thumbs up> to this message!".format(auth.mention, amount)
            await member.dm_channel.send(message)
    else:
        await ctx.send("Please send me messages only in the expenses channel!")


@bot.command()
async def check(ctx):
    mentions = ctx.message.mentions
    me = bot.get_user(325320332971999244)
    if me.dm_channel is None:
        await me.create_dm()
    await me.dm_channel.send(mentions[0].mention)


bot.run(os.getenv('TOKEN'))
