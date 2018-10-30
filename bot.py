import asyncio
import os
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
    return len(message.mentions) > 0 and get_amount(message) is not None and message.channel.name == "expenses" and message.content.split(" ")[0] == '!paid'


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
    """Verifies a payment"""
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)
    message = await channel.get_message(payload.message_id)
    mentions = message.mentions
    print("i was here")
    if not is_DM(channel) and channel.name == "expenses" and user in mentions and str(payload.emoji)[0] == "👍" and fine_paid_message(message):
        await db_connector.verify(paid_for=user, payee=message.author, amount=get_amount(message), guild_id=message.guild.id, message_id=message.id)
        print("lol")


@bot.command()
async def paid(ctx):
    """!paid <mentions> amount <description>"""
    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "expenses":
        if not fine_paid_message(ctx.message):
            await ctx.send("Use `!help paid` to see the format")
        else:
            message = ctx.message
            mentions = message.mentions
            await db_connector.pay(guild_id=message.guild.id, payee=message.author, paid_for=mentions, amount=get_amount(message), message=message)
    else:
        await ctx.send("This command can be used only in `expenses` channel")


@bot.command()
async def stats(ctx):
    """Shows the current stats of a member regarding his/her expenses"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_data(guild_id=ctx.message.guild.id, user=ctx.message.author)
        msg = ""
        for member in results.keys():
            if results[member] >= 0:
                msg += bot.get_user(int(member)).name + " owes you " + str(results[member])
            else:
                msg += "\nYou owe " + bot.get_user(int(member)).name + " " + str(results[member])

        await ctx.send("`"+msg+"`")

    else:
        await ctx.send("This command can be used only in `current_stats` channel")


@bot.command()
async def unverified(ctx):
    """Shows all the members unverified payments"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_unverified(user=ctx.message.author, guild_id=ctx.message.guild.id)
        msg = ""
        for result in results:
            msg += result['message']+"\n"

        await ctx.send("`"+msg+"`")
    else:
        await ctx.send("This command can be used only in `current_stats` channel")


@bot.command()
async def transactions(ctx):
    """Displays last 10 transaction made by the user"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_transactions(guild_id=ctx.message.guild.id, user=ctx.message.author)
        msg = ""
        for result in results:
            msg += result['message'] + "\n"

        await ctx.send("`"+msg+"`")
    else:
        await ctx.send("This command can be used only in `current_stats` channel")

print(len("👍🏽"))
bot.run(os.getenv('TOKEN'))
