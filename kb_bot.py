#!/usr/bin/env python3
import random
import shlex
import subprocess
import time

from kb_chat_api import KeybaseChat


def check_command(message):
    """Check if message is a command, and react accordingly"""
    try:
        command = shlex.split(message)
    except ValueError as e:
        print('error parsing message.')
        print('message:', message)
        print('error:', e)
        return [0, None]

    # return [response_code, response, user (optional)]
    #
    # response_code:
    # 0 = no response necessary
    # 1 = generic response
    # 2 = @mention response
    # 3 = pm response
    # 4 = pm <user> response.

    if command[0].lower() == '!uptime' and len(command) == 1:
        uptime = subprocess.check_output(["uptime"]).decode('utf-8')
        return [1, uptime]
    elif command[0].lower() == '!ping' and len(command) == 1:
        return [2, 'pong!']
    elif command[0].lower() == '!roll':
        try:
            num_of_dice = int(command[1])
            num_of_sides = int(command[2]) + 1
        except ValueError:
            num_of_dice = 0
            num_of_sides = 0
        if (num_of_dice not in range(1, 11) or
                num_of_sides not in range(3, 101)):
            num_of_dice = 2
            num_of_sides = 7
        dice = []
        for _ in range(num_of_dice):
            dice.append(random.choice(range(1, num_of_sides)))
        res = 'You rolled a '
        for n in dice[0:-1]:
            res += '`{}`, '.format(n)
        res += 'and `{}`, for a total of `{}`.'.format(dice[-1], sum(dice))
        return [2, res]
    elif command[0].lower() == '!help' and len(command) == 1:
        command_list = '''```
!help
    This message.

!ping
    Will respond with pong!

!roll <x> <y>
    Roll x number of y sided dice. If x and y are not provided, defaults to 2 6-sided dice. x must be integer from 1 and 10, and y must be integer from 2 to 100.

!uptime
    Will respond with server uptime.
```'''
        return [1, command_list]
    return [0, None]


if __name__ == '__main__':
    kb = KeybaseChat()

    # Team channels to monitor
    channels = {
            'crbot.public': ['bots'],
            }

    # Determine if this is the first loop so we can clear unread messages
    # without responding to them. Otherwise we might flood channels or users
    # with a bunch of responses to old messages. You can set this to False
    # if you want to reply to all unread messages at startup
    first_loop = True

    while True:
        conversations = kb.get_conversations()

        # Respond to team messages
        teams = [team for team in conversations['teams'] if team in channels]
        for team in teams:
            unread_channels = [
                    channel for channel in channels[team]
                    if conversations['teams'][team][channel]['unread']
                    ]
            for channel in unread_channels:
                messages = kb.get_team_messages(team, channel=channel)
                for key, message in messages.items():
                    # message information
                    body = message['body']
                    sender = message['sender']

                    if not first_loop:
                        # check_command results
                        res = check_command(body)
                        res_code = res[0]
                        msg = res[1]

                        if res_code > 0:
                            print('-' * 20)
                            print('Team command received')
                            print('  -Team:', team)
                            print('  -Channel:', channel)
                            print('  -Sender:', sender)
                            print('  -Message:', body)
                            print('  -Response:', res)

                        if res_code == 0:
                            # 0 = no response necessary
                            pass
                        elif res_code == 1:
                            # 1 = generic response
                            kb.send_team_message(team, msg, channel=channel)
                        elif res_code == 2:
                            # 2 = @mention response
                            msg = '@{}, {}'.format(sender, msg)
                            kb.send_team_message(team, msg, channel=channel)
                        elif res_code == 3:
                            # 3 = pm response
                            kb.send_user_message(sender, msg)
                        elif res_code == 4:
                            # 4 = pm <user> response.
                            msg = msg
                            user = res[2]
                            kb.send_user_message(user, msg)

        # Respond to individual messages
        users = [
                user for user in conversations['individuals']
                if conversations['individuals'][user]['unread']
                ]
        for user in users:
            messages = kb.get_user_messages(user)
            for key, message in messages.items():
                # message information
                body = message['body']
                sender = message['sender']

                if not first_loop:
                    # check_command results
                    res = check_command(body)
                    res_code = res[0]
                    msg = res[1]

                    if res_code > 0:
                        print('-' * 20)
                        print('PM command received')
                        print('  -User:', user)
                        print('  -Message:', body)
                        print('  -Response:', res)

                    if res_code == 0:
                        # 0 = no response necessary
                        pass
                    elif res_code == 1 or res_code == 2 or res_code == 3:
                        # 1 = generic response
                        # 2 = @mention response
                        # 3 = pm response
                        kb.send_user_message(sender, msg)
                    elif res_code == 4:
                        # 4 = pm <user> response.
                        msg = msg
                        user = res[2]
                        kb.send_user_message(user, msg)
        if first_loop:
            first_loop = False
        time.sleep(1)
