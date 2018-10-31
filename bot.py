
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

    allowed = "()[]{}+-*/^0123456789"
    expression = []

    for token in message.content:
        if token in allowed:
            if token == '^':
                token = '**'
            expression.append(token)
    return int(round(eval(''.join(expression))))


def fine_paid_message(message):
    """Returns true if the format of paid message is fine"""
    return (len(message.mentions) > 0 or message.mention_everyone) \
           and get_amount(message) is not None \
           and message.channel.name == "expenses" \
           and message.content.split(" ")[0] == '!paid'


def remove_bots(members):
    """Removes bots from a list of members"""
    bots = []
    for member in members:
        if member.bot:
            bots.append(member)
    for bot in bots:
        members.remove(bot)

    return members

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
    if payload.user_id == 505263369176219658: #Saul's ID
        return
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)

    message = await channel.get_message(payload.message_id)
    if message.mention_everyone:
        mentions = remove_bots(message.guild.members)
    else:
        mentions = message.mentions

    if not is_DM(channel) and channel.name == "expenses" and user in mentions and str(payload.emoji)[0] == "👍" and fine_paid_message(message):
        await db_connector.verify(paid_for=user, payee=message.author, amount=get_amount(message), guild_id=message.guild.id, message_id=message.id)


@bot.command()
async def paid(ctx):
    """!paid <mentions> amount <description>"""
    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "expenses":
        if not fine_paid_message(ctx.message):
            await ctx.send("Use `!help paid` to see the format")
        else:
            message = ctx.message
            if message.mention_everyone:
                mentions = ctx.message.guild.members
                mentions.remove(message.author)
            else:
                mentions = message.mentions
                if mentions.count(ctx.message.guild.get_member(ctx.author.id)) > 0:
                    await ctx.send("`You can't pay for yourself!`")
                    return
            mentions = remove_bots(mentions)
            print(mentions)
            await db_connector.pay(guild_id=message.guild.id, payee=message.author, paid_for=mentions, amount=get_amount(message), message=message)
            await ctx.message.add_reaction("👍🏽")

    else:
        await ctx.send("This command can be used only in `expenses` channel")


@bot.command()
async def stats(ctx):
    """Shows the current stats of a member regarding his/her expenses"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_data(guild_id=ctx.message.guild.id, user=ctx.message.author)
        if results == -1:
            await ctx.send("`No stats to show`")
            return

        msg = ""
        for member in results.keys():
            if results[member] >= 0:
                msg += bot.get_user(int(member)).name + " owes you " + str(results[member])+"\n"
            else:
                msg += "You owe " + bot.get_user(int(member)).name + " " + str(results[member])+"\n"

        await ctx.send("`"+msg+"`")

    else:
        await ctx.send("This command can be used only in `current_stats` channel")


@bot.command()
async def unverified(ctx):
    """Shows all the members unverified payments"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_unverified(user=ctx.message.author, guild_id=ctx.message.guild.id)
        if results == -1:
            await ctx.send("`No Unverified transactions`")
            return

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
        if results == -1:
            await ctx.send("`No transactions to show`")
            return

        msg = ""
        for result in results:
            msg += result['message'] + "\n"

        await ctx.send("`"+msg+"`")
    else:
        await ctx.send("This command can be used only in `current_stats` channel")


bot.run(os.getenv('TOKEN'))
