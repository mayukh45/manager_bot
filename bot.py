import asyncio
import os
import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands

desc = 'A bot made by Mayukh to manage expenses'
loop = asyncio.get_event_loop()
bot = Bot(command_prefix=commands.when_mentioned_or("!"), description=desc, loop=loop)

@bot.event
async def on_raw_reaction_add(payload):
    print("LOLWA")
    if str(payload.emoji) == "👌🏽":
        print("damn")


@bot.command()
async def paid(ctx,arg):
    print(ctx.message.content)
TOKEN = "NTA1MjYzMzY5MTc2MjE5NjU4.DrRFKw.2Qi118fX_L6eFECd4dBocQdn7D0"
bot.run(TOKEN)