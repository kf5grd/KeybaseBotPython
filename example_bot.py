#!/usr/bin/env python3
import random
import time

from shlex import split
from keybase_chat_api import KeybaseChat, KeybaseBot


# Team channels to monitor
channels = {
        'crbot.public': ['bots'],
        }

kb = KeybaseChat()
bot = KeybaseBot(kb, channels, help_command=r'^\.help', help_trigger='.help')


@bot.command(r'^\.ping', help_trigger='.ping')
def ping_cmd(message_data):
    """Respond with 'pong!'"""
    response_text = 'pong!'
    return bot.respond(response_text, message_data, at_mention=True)


@bot.command(r'\b(fuck|shit|ass|pussy|bitch)\b', show_help=False)
def swear_cmd(message_data):
    """Respond to swear words"""
    response_text = "Please dont use that kind of language in here."
    return bot.respond(response_text, message_data, at_mention=True)


@bot.command(r'^\.roll', help_trigger='.roll <dice> <sides>')
def roll_cmd(message_data):
    '''Roll <dice> amount of <side>-sided dice. If <dice> and <sides> are not
    provided, default is to roll 2 6-sided dice. If <dice> and <sides> are
    provided, <dice> must be between 1 and 10, and <sides> must be between 2
    and 100.'''
    try:
        num_of_dice = int(split(message_data['body'])[1])
        num_of_sides = int(split(message_data['body'])[2]) + 1
    except ValueError:
        num_of_dice = 0
        num_of_sides = 0
    except IndexError:
        num_of_dice = 2
        num_of_sides = 7
    if (num_of_dice not in range(1, 11) or
        num_of_sides not in range(2, 102)):
        response_text = '`<dice>` must be a number from 1 to 10, and ' \
                        '`<sides>` must be a number from 2 to 100'
        return bot.respond(response_text, message_data, at_mention=True)
    dice = []
    for _ in range(num_of_dice):
        dice.append(random.choice(range(1, num_of_sides)))
    response_text = 'You rolled a '
    for n in dice[0:-1]:
        response_text += '`{}`, '.format(n)
    response_text += 'and `{}`, for a total of `{}`.'.format(dice[-1],
                                                             sum(dice))
    return bot.respond(response_text, message_data, at_mention=True)


# Clear out any unread messages received while bot was offline
bot.check_messages(respond=False)

# Watch for new messages
while True:
    bot.check_messages()
    time.sleep(1)
