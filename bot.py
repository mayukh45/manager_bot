import asyncio
import os
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from mongodb_connector import MongoDBConnector
from checks import get_amount, is_DM, fine_paid_message, remove_bots

desc = 'A bot made by Mayukh to manage expenses, Interact with the bot only in the expenses channel'

db_name = 'manager_db'
loop = asyncio.get_event_loop()
db_connector = MongoDBConnector(os.getenv('MONGODB_SRV'), db_name='manager_db', loop=loop)
bot = Bot(command_prefix=commands.when_mentioned_or("!"), description=desc, loop=loop)
bot.remove_command('help')


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
    author_id = message.author.id

    if message.mention_everyone:
        mentions = remove_bots(message.guild.members)
    else:
        mentions = message.mentions

    if not is_DM(channel) and channel.name == "expenses" and user in mentions and str(payload.emoji)[0] == "👍" and fine_paid_message(message) :
        if author_id != 505263369176219658:
            await db_connector.verify(paid_for=user, payee=message.author, amount=get_amount(message), guild_id=message.guild.id, message_id=message.id)
        else:
            print(message.content[3:11])
            if message.content[3:11] == "Payments":
                pass


@bot.command()
async def paid(ctx):
    """!paid <mentions> amount <description>"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "expenses":
        if not fine_paid_message(ctx.message):
            await ctx.send("```Use !help paid to see the format```")
        else:
            message = ctx.message
            if message.mention_everyone:
                mentions = ctx.message.guild.members
                mentions.remove(message.author)
            else:
                mentions = message.mentions
                if mentions.count(ctx.message.guild.get_member(ctx.author.id)) > 0:
                    await ctx.send("```You can't pay for yourself!```")
                    return
            mentions = remove_bots(mentions)
            await db_connector.pay(guild_id=message.guild.id, payee=message.author, paid_for=mentions, amount=get_amount(message), message=message)
            await ctx.message.add_reaction("👍🏽")

    else:
        await ctx.send("```This command can be used only in expenses channel```")


@bot.command()
async def stats(ctx):
    """Shows the current stats of a member regarding his/her expenses"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_data(guild_id=ctx.message.guild.id, user=ctx.message.author)
        if results == -1:
            await ctx.send("```No stats to show```")
            return

        msg = ""
        for member in results.keys():
            if str(ctx.message.author.id) == member:
                msg += "Your total expenditure till now is {0}".format(results[member])

            elif results[member] > 0:
                msg += bot.get_user(int(member)).name + " owes you " + str(results[member])+"\n"
            elif results[member] < 0:
                msg += "You owe " + bot.get_user(int(member)).name + " " + str(abs(results[member]))+"\n"

        await ctx.send("```"+msg+"```")

    else:
        await ctx.send("```This command can be used only in current_stats channel```")


@bot.command()
async def unverified(ctx):
    """Shows all the members unverified payments"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_unverified(user=ctx.message.author, guild_id=ctx.message.guild.id)
        if results == -1:
            await ctx.send("```No Unverified transactions```")
            return

        msg = "Your unverified payments\n"
        for result in results:
            msg += result['message']+"\n"

        await ctx.send("```"+msg+"```")
    else:
        await ctx.send("```This command can be used only in current_stats channel```")


@bot.command()
async def unapproved(ctx):
    """Shows all the members unverified payments"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_unapproved(user=ctx.message.author, guild_id=ctx.message.guild.id)
        if results == -1:
            await ctx.send("```No Unapproved transactions```")
            return

        msg = "Payments you did not approve\n"
        for result in results:
            msg += result['message']+"\n"

        await ctx.send("```"+msg+"```")
    else:
        await ctx.send("```This command can be used only in current_stats channel```")


@bot.command()
async def transactions(ctx):
    """Displays last 10 transaction made by the user"""

    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "current_stats":
        results = await db_connector.get_transactions(guild_id=ctx.message.guild.id, user=ctx.message.author)
        if results == -1:
            await ctx.send("```No transactions to show```")
            return

        msg = "Your last 10 transactions\n"
        for result in results:
            msg += result['message'] + "\n"

        await ctx.send("```"+msg+"```")
    else:
        await ctx.send("```This command can be used only in current_stats channel```")


@bot.command()
async def help(ctx):
    msg = "`@mention me or use ! before my supported commands`"
    embed = discord.Embed(title="Supported Commands")

    embed.add_field(name='paid', value='Use this when you are paying for someone. '
                                       'The format is: `!paid mentions(ie the members '
                                       'of the guild you are paying for) amount < description >` , '
                                       'You can also give equations in place of amount like '
                                       '!paid mentions 100/4 < desc > also works! \n'
                                       ' `Example` ```!paid @Jack 500```')
    embed.add_field(name='unverified', value='This shows a list of your unverified payments, '
                                             'A payment (ie made using the paid command)'
                                             ' is verified only if the members you paid for thumbs up your message.')
    embed.add_field(name='stats', value='This can be used to know your current stats, '
                                        'like how much you owe someone or someone else owes you!')
    embed.add_field(name='transactions', value='This shows your last 10 transactions.')
    embed.add_field(name='unapproved', value="This shows the payments you did not approve yet, One needs "
                                             "to approve payments (made by `paid` command) by thumbing up the payments "
                                             "in which he/she is mentioned")
    await ctx.send(msg, embed=embed)


@bot.command()
async def self(ctx):
    if not is_DM(ctx.message.channel) and ctx.message.channel.name == "expenses":

        await db_connector.add_self(guild_id=ctx.message.guild.id, message=ctx.message,
                                    user=ctx.message.author, amount=get_amount(ctx.message))
    else:
        await ctx.send("```This command can be used only in expenses channel```")


@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed(title="Command not found!", description="Use !help "
                                                                  "to see the available commands")

    if type(error) is discord.ext.commands.errors.CommandNotFound:
        await ctx.send(embed=embed)


@bot.event
async def on_ready():
    game = discord.Game(name="Money laundering")
    await bot.change_presence(status=discord.Status.online, activity=game)


bot.run(os.getenv('TOKEN'))
