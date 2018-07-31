import json
import argparse
import logging
from os import getenv

from comm import platforms


class CLI(argparse.ArgumentParser):
    """
    The main utility for a command line interface for generalized
    mass-messaging, capable of fully processing all external resources
    used by the script.
    """

    def __init__(self):
        super().__init__()
        self.add_platform_arg()
        self.add_recipients_arg()
        self.add_content_arg()
        self.add_sender_arg()

    def add_platform_arg(self):
        self.add_argument(
            'platform',
            help='The platform over which to send the message'
        )

    def add_content_arg(self):
        self.add_argument(
            'content',
            help='The text to use as the body of the message'
        )

    def add_recipients_arg(self):
        self.add_argument(
            'recipients',
            help='List of recipients to send to',
            nargs='*'
        )

    def add_sender_arg(self):
        self.add_argument(
            '-s',
            '--sender',
            help='The JSON data for the sender'
        )

    @classmethod
    def fill_in_args(cls,
                     platform_name,
                     sender_json,
                     recipients_text,
                     content):
        """
        Attempts to fill in null command line arguments.
        :param platform_name: The name of the platform over which to
        send messages
        :param sender_json: The platform-specific JSON data
        representing the sender
        :param recipients_text: A list of platform-specific textual
        representations of recipients
        :param content: The content of the messages
        :return: A dictionary of the key value pairs reflecting the
        arguments to this function after attempting to fill in null
        values
        """
        if sender_json is None:
            logging.debug('Sender not specified in command line args. '
                          'Attempting to load from environment variables.')
            sender_env_name = \
                'comm_{}_sender'.format(platform_name).upper()
            sender_path = getenv(sender_env_name)
            if sender_path is not None:
                with open(sender_path, 'r') as f:
                    sender_json = f.read()
            else:
                raise ValueError('No sender specified. Please specify one '
                                 'via command line or environment variables.')
        return {
            'platform_name': platform_name,
            'sender_json': sender_json,
            'recipients_text': recipients_text,
            'content': content
        }

    @classmethod
    def agnostic_parse(cls,
                       platform_name,
                       sender_json,
                       recipients_text,
                       content):
        """
        Parses raw arguments (as from the command line) into
        program-agnostic data representations.  Returns the following:
        - platform_name: The name of the platform over which to send
          messages
        - sender_data: A platform-specific dictionary representing the
          sender
        - recipients_data: A list of platform-specific representations
          of recipients
        - content: The content of the messages
        :param platform_name: The name of the platform over which to
        send messages
        :param sender_json: The platform-specific JSON data
        representing the sender
        :param recipients_text: A list of platform-specific textual
        representations of recipients
        :param content: The content of the messages
        :return: A dictionary containing the key value pairs described
        above
        """
        sender_data = json.loads(sender_json)
        recipients_data = []
        for recipient_text in recipients_text:
            try:
                recipient_data = json.loads(recipient_text)
            except json.JSONDecodeError:
                logging.debug('Recipient text \'{}\' could not be decoded as '
                              'JSON and will be passed as a string.'
                              .format(recipient_text), exc_info=True)
                recipient_data = recipient_text
            recipients_data.append(recipient_data)
        return {
            'platform_name': platform_name,
            'sender_data': sender_data,
            'recipients_data': recipients_data,
            'content': content
        }

    def get_args(self):
        """
        Loads and processes all external resources used by the script.
        The resources are as follows:
        - platform_name: The name of the platform over which to send
          messages
        - sender_data: A platform-specific dictionary representing
          the sender
        - recipients_data: A list of platform-specific
          representations of recipients
        - content: The content of the messages
        :return: A dictionary containing the key value pairs described
        above
        """
        args = self.parse_args()
        return self.agnostic_parse(**self.fill_in_args(args.platform,
                                                       args.sender,
                                                       args.recipients,
                                                       args.content))


def build_resources(platform_name,
                    sender_data,
                    recipients_data,
                    content):
    """
    Parses program-agnostic data representations into
    platform-specific classes.  The resources are as follows:
    - platform: An instance of the `comm.platform.Platform`
      subclass corresponding to the given platform name
    - sender: An instance of the `comm.platform.ClientUser`
      subclass corresponding to the given platform name
    - recipients: A list of instances of the `comm.platform.User`
      subclass corresponding to the given platform name
    - content: The content of the messages
    :param platform_name: The name of the platform over which to
    send messages
    :param sender_data: A platform-specific dictionary representing
    the sender
    :param recipients_data: A list of platform-specific
    representations of recipients
    :param content: The content of the messages
    :return: A dictionary containing the key value pairs described
    above
    """
    platform = platforms.platform_class[platform_name]()
    sender = platform.build_sender(sender_data)
    recipients = [platform.build_recipient(recipient_data)
                  for recipient_data in recipients_data]
    return {
        'platform': platform,
        'sender': sender,
        'recipients': recipients,
        'content': content
    }


class Message:
    """
    A generic message capable of sending itself.  Necessary because
    while a sender can deliver content to a recipient, it does not
    store the content or recipient.
    """

    def __init__(self, sender, recipient, content):
        self.sender = sender
        self.recipient = recipient
        self.content = content

    def send(self):
        self.sender.send_message(self.recipient, self.content)


def build_messages(sender, recipients, content):
    """
    Produces a list of messages, one per recipient, all with the same
    sender and content.
    :param sender: An instance of the `comm.platform.ClientUser`
    subclass corresponding to the platform over which the message will
    be sent
    :param recipients: A list of instances of the `comm.platform.User`
    subclass corresponding to the platform over which the message will
    be sent
    :param content: The content of the messages
    :return: A list of `comm.basic.Message` objects
    """
    return [Message(sender, recipient, content) for recipient in recipients]


def send_message(message):
    """
    Sends a message and logs the result.
    :param message: The message to send
    """
    recipient_id = message.recipient.get_id()
    try:
        message.send()
        logging.info('Successfully sent message to {}:\n{}'
                     .format(recipient_id, message.content))
    except Exception:
        logging.error('Failed to send message to {}.'
                      .format(recipient_id), exc_info=True)


def _send_to_all(sender, recipients, content):
    """
    Requires instances of platform-specific classes; for internal use.
    """
    messages = build_messages(**locals())
    for message in messages:
        send_message(message)


def send_to_all(platform_name,
                sender_data,
                recipients_data,
                content):
    """
    Sends the same content to multiple recipients.
    :param platform_name: The name of the platform over which to send
    messages
    :param sender_data: A platform-specific dictionary representing
    the sender
    :param recipients_data: A list of platform-specific
    representations of recipients
    :param content: The content of the messages
    """
    resources = build_resources(**locals())
    _send_to_all(resources['sender'],
                 resources['recipients'],
                 resources['content'])
