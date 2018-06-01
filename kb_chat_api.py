#!/usr/bin/env python3
import json
import subprocess

from shlex import split


class KeybaseChat:

    def __init__(self):
        self.username = self._get_username()

    def __repr__(self):
        return 'KeybaseChat()'

    def _send_chat_api(self, api_command):
        """Send a JSON formatted request to the chat api.

        This takes a dictionary and sends it as a JSON request to the Keybase
        chat api. You can get a full list of supported API commands by running
        the following command in the terminal:
            keybase chat api --help

        Args:
            api_command (dict): API command to send.

        Returns:
            dict: Response from API
        """
        command = "keybase chat api -m '{}'".format(
                json.JSONEncoder().encode(api_command))
        response = subprocess.check_output(split(command))
        return json.loads(response.decode('utf-8'))

    def _get_username(self):
        """Return the username of the current user from the keybase CLI."""
        command = subprocess.check_output(['keybase', 'status', '-j'])
        keybase_status = json.loads(command.decode('utf-8'))
        return keybase_status.get('Username')

    def get_conversations(self):
        '''Return a dictionary with all active conversations.

        This method will return a dictionary containing all active
        conversations. The dictionary will be formatted as follows:

        {
            "teams": {
                "team1": {
                    "channel1": {
                        "unread": True
                    },
                    "channel2": {
                        "unread": False
                    }
                },
                "team2": {
                    "channel1": {
                        "unread": False
                    },
                    "channel2": {
                        "unread": True
                    }
                }
            },
            "individuals": {
                "individual1": {
                    "unread": True
                },
                "individual2": {
                    "unread": False
                }
            }
        }
        '''
        api_command = {
            "method": "list",
            "params": {
                "options": {
                    "topic_type": "CHAT"
                }
            }
        }
        conversations_dict = self._send_chat_api(api_command)
        result = {
            "teams": {},
            "individuals": {},
        }
        for conversation in conversations_dict['result']['conversations']:
            unread = conversation['unread']
            if conversation['channel']['members_type'] == 'team':
                team_name = conversation['channel']['name']
                topic_name = conversation['channel']['topic_name']
                try:
                    result['teams'][team_name][topic_name] = {}
                except KeyError:
                    result['teams'][team_name] = {}
                    result['teams'][team_name][topic_name] = {}
                finally:
                    result['teams'][team_name][topic_name]['unread'] = unread
            else:
                whole_name = conversation['channel']['name']
                name = whole_name.replace(self.username, '').replace(',', '')
                result['individuals'][name] = {}
                result['individuals'][name]['unread'] = unread
        return result.copy()

    def send_team_message(self, team, message, channel='general'):
        """Send message to a team channel.

        Args:
            team (str): Team name
            message (str): Message to send to the channel

        Optional Args:
            channel (str): Channel name within the team

        Returns:
            dict: Response from API
        """
        api_command = {
            "method": "send",
            "params": {
                "options": {
                    "channel": {
                        "name": team,
                        "members_type": "team",
                        "topic_name": channel
                    },
                    "message": {
                        "body": message
                    }
                }
            }
        }
        return self._send_chat_api(api_command)

    def send_user_message(self, user, message):
        """Send message to a single user.

        Args:
            user (str): User's username
            message (str): Message to send to the user

        Returns:
            dict: Response from API
        """
        api_command = {
            "method": "send",
            "params": {
                "options": {
                    "channel": {
                        "name": "{},{}".format(self.username, user)
                    },
                    "message": {
                        "body": message
                    }
                }
            }
        }
        return self._send_chat_api(api_command)

    def get_team_messages(self, team, channel='general'):
        """Return new messages from team channel.

        Args:
            team (str): Team name

        Optional Args:
            channel (str): Channel name within the team

        Returns dict formatted as follows:

        {
            "63": {
                "sender": "username2",
                "body": "message 3"
            },
            "62": {
                "sender": "username2",
                "body": "message 2"
            },
            "61": {
                "sender": "username1",
                "body": "message 1",
            }
        }
        """
        api_command = {
            "method": "read",
            "params": {
                "options": {
                    "channel": {
                        "name": team,
                        "members_type": "team",
                        "topic_name": channel
                    }
                }
            }
        }
        response = {}
        messages = self._send_chat_api(api_command)['result']['messages']
        for message in messages:
            if message['msg']['unread']:
                if message['msg']['content']['type'] == 'text':
                    message_id = str(message['msg']['id'])
                    sender = message['msg']['sender']['username']
                    body = message['msg']['content']['text']['body']
                    response[message_id] = {}
                    response[message_id]['sender'] = sender
                    response[message_id]['body'] = body
        return response

    def get_user_messages(self, user):
        """Return new messages from user.

            return response
            user (str): User's username

        Returns dict formatted as follows:

        {
            "63": {
                "sender": "username",
                "body": "message 3"
            },
            "62": {
                "sender": "username",
                "body": "message 2"
            },
            "61": {
                "sender": "username",
                "body": "message 1",
            }
        }
        """
        api_command = {
            "method": "read",
            "params": {
                "options": {
                    "channel": {
                        "name": "{},{}".format(self.username, user),
                    }
                }
            }
        }
        response = {}
        for message in self._send_chat_api(api_command)['result']['messages']:
            if message['msg']['unread']:
                if message['msg']['content']['type'] == 'text':
                    message_id = message['msg']['id']
                    sender = message['msg']['sender']['username']
                    body = message['msg']['content']['text']['body']
                    response[message_id] = {}
                    response[message_id]['sender'] = sender
                    response[message_id]['body'] = body
        return response


class KeybaseBot:
    def __init__(self, keybase_api, channels, help_command='!help'):
        self.command = self._command_registry()
        self.kb = keybase_api
        self.channels = channels
        self._commands[help_command] = {
                'f': self.help_cmd,
                'command': help_command,
                'args': None,
                'help': self.help_cmd.__doc__
                }
        self.commands = self.get_commands()

    def _command_registry(self, *args):
        self._commands = {}

        def make_command(*args, **kwargs):
            try:
                cmd = args[0]
            except IndexError:
                raise ValueError('Must provide command trigger')
            cmd_args = kwargs.get('args')

            def decorator(func, *args, **kwargs):
                def wrapper(func):
                    self._command_name = cmd
                    self._commands[self._command_name] = {}
                    self._commands[self._command_name]['f'] = func
                    self._commands[self._command_name]['command'] = cmd
                    self._commands[self._command_name]['args'] = cmd_args
                    self._commands[self._command_name]['help'] = func.__doc__
                    return func
                return wrapper(func)
            return decorator
        return make_command

    def get_commands(self):
        return self._commands.copy()

    def check_messages(self, respond=True):
        conversations = self.kb.get_conversations()

        # Respond to team messages
        teams = [team for team in conversations['teams']
                 if team in self.channels]
        for team in teams:
            unread_channels = [
                    channel for channel in self.channels[team]
                    if conversations['teams'][team][channel]['unread']
                    ]
            for channel in unread_channels:
                messages = self.kb.get_team_messages(team, channel=channel)
                for key, message in messages.items():
                    # message information
                    message_data = {
                            'type': 'team',
                            'body': message['body'],
                            'sender': message['sender'],
                            'team': team,
                            'channel': channel
                            }
                    if respond:
                        try:
                            found_cmd = split(message['body'])[0]
                        except ValueError:
                            found_cmd = message['body']
                        if found_cmd in self.get_commands():
                            trigger = split(message['body'])[0]
                            trigger_func = self.get_commands()[trigger]['f']
                            print('-' * 15)
                            print('Trigger found: {}'.format(trigger))
                            print('  Team: {}'.format(team))
                            print('  Channel: {}'.format(channel))
                            print('  Sender: {}'.format(message['sender']))
                            result = trigger_func(message_data)
                            print('  Result: {}'.format(result))

        # Respond to private messages
        users = [
                user for user in conversations['individuals']
                if conversations['individuals'][user]['unread']
                ]
        for user in users:
            messages = self.kb.get_user_messages(user)
            for key, message in messages.items():
                # message information
                message_data = {
                        'type': 'individual',
                        'body': message['body'],
                        'sender': message['sender']
                        }
                if respond:
                    try:
                        found_cmd = split(message['body'])[0]
                    except ValueError:
                        found_cmd = message['body']
                    if found_cmd in self.get_commands():
                        trigger = split(message['body'])[0]
                        trigger_func = self.get_commands()[trigger]['f']
                        print('-' * 15)
                        print('Trigger found: {}'.format(trigger))
                        print('  Sender: {}'.format(message['sender']))
                        result = trigger_func(message_data)
                        print('  Result: {}'.format(result))

    def respond(self, response_text, message_data, at_mention=False):
        if message_data['type'] == 'team':
            _at = ''
            if at_mention:
                _at = '@{}, '.format(message_data['sender'])
            res = self.kb.send_team_message(message_data['team'],
                                            '{}{}'.format(
                                                _at,
                                                response_text),
                                            channel=message_data['channel'])
        elif message_data['type'] == 'individual':
            res = self.kb.send_user_message(message_data['sender'],
                                            response_text)
        return json.dumps(res)

    def help_cmd(self, message_data):
        '''Show available commands'''
        help_text = ''
        all_cmds = self.get_commands()
        for cmd in all_cmds:
            trigger = all_cmds[cmd]['command']
            cmd_help = all_cmds[cmd]['help']
            if all_cmds[cmd]['args']:
                args = ' {}'.format(all_cmds[cmd]['args'])
            else:
                args = ''
            help_text += '`{}{}`\n'.format(trigger, args)
            help_text += '```    {}```\n\n'.format(cmd_help)
        if message_data['type'] == 'team':
            res = self.kb.send_team_message(message_data['team'],
                                            help_text,
                                            channel=message_data['channel'])
        elif message_data['type'] == 'individual':
            res = self.kb.send_user_message(message_data['sender'],
                                            help_text)
        return json.dumps(res)


if __name__ == '__main__':
    pass
