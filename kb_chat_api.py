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
        keybase_status = subprocess.check_output(['keybase', 'status'],
                                                 universal_newlines=True)
        for line in keybase_status.split('\n'):
            if line.startswith('Username'):
                return line.split(' ')[-1]
        return None

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


if __name__ == '__main__':
    pass
