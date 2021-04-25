import discord


def is_int(val):
    try:
        a = int(val)
    except:
        return False
    return True


def is_DM(channel):
    """Returns True if the expenses channel is a DM channel"""
    return type(channel) is discord.channel.DMChannel


def get_amount(message):
    """Get the amount of money from a message"""

    allowed = "()[]{}+-*/^0123456789."
    expression, hide = [], 0

    for token in message.content:
        if token == '<':
            hide += 1
        if hide == 0 and token in allowed:
            if token == '^':
                token = '**'
            expression.append(token)
        if token == '>':
            hide -= 1
    if len(expression) == 0:
        return None
    else:
        return int(round(eval(''.join(expression))))


def fine_paid_message(message):
    """Returns true if the format of paid message is fine"""
    return (len(message.mentions) > 0 or message.mention_everyone) and get_amount(message) is not None and message.channel.name == "expenses" and (message.content.split(" ")[0] == '!paid' or message.content.split(" ")[0] == '<@505263369176219658>')


def remove_bots(members):
    """Removes bots from a list of members"""
    bots = []
    for member in members:
        if member.bot:
            bots.append(member)
    for bot in bots:
        members.remove(bot)

    return members
