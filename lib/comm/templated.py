import json
import logging
import sys
import yaml
from os import getenv

from comm import platforms
from comm import basic
from comm.user_table import UserTable


class CLI(basic.CLI):
    """
    The main utility for a command line interface for templated
    mass-messaging, capable of fully processing all external resources
    used by the script.
    """

    def __init__(self):
        super().__init__()
        self.add_data_arg()
        self.add_user_table_arg()

    def add_data_arg(self):
        self.add_argument(
            'data',
            help='The JSON data used for filling the content template',
            nargs='?'
        )

    def add_recipients_arg(self):
        self.add_argument(
            '-r',
            '--recipients',
            help='List of recipients to send to',
            nargs='*',
            default=[]
        )

    def add_user_table_arg(self):
        self.add_argument(
            '--user-table',
            help='YAML text representing a list of users, where a user is a '
                 'mapping of platform names to lists of usernames',
        )

    @classmethod
    def fill_in_args(cls,
                     platform_name,
                     sender_json,
                     recipients_text,
                     content,
                     templating_data_json,
                     user_table_yaml):
        """
        Attempts to fill in null command line arguments.
        :param platform_name: The name of the platform over which to
        send messages
        :param sender_json: The platform-specific JSON data
        representing the sender
        :param recipients_text: A list of platform-specific textual
        representations of recipients
        :param content: The template for the content of the messages
        :param templating_data_json: JSON representing the full set of
        data used to fill the template
        :param user_table_yaml: YAML representing a list of users,
        where a user is a mapping of platform names to lists of
        :return: A dictionary of the key value pairs reflecting the
        arguments to this function after attempting to fill in null
        values
        """
        if templating_data_json is None:
            logging.debug('Data not specified in command line args. Reading '
                          'from stdin.')
            templating_data_json = sys.stdin.read()
        if user_table_yaml is None:
            logging.debug('User table not specified in command line args. '
                          'Attempting to load from environment variables.')
            user_table_path = getenv('comm_user_table'.upper())
            if user_table_path is not None:
                with open(user_table_path, 'r') as f:
                    user_table_yaml = f.read()
            else:
                raise ValueError('No user table specified. Please specify '
                                 'one via command line or environment '
                                 'variables.')
        return {
            **super().fill_in_args(platform_name,
                                   sender_json,
                                   recipients_text,
                                   content),
            'templating_data_json': templating_data_json,
            'user_table_yaml': user_table_yaml
        }

    @classmethod
    def agnostic_parse(cls,
                       platform_name,
                       sender_json,
                       recipients_text,
                       content,
                       templating_data_json,
                       user_table_yaml):
        """
        Parses raw arguments (as from the command line) into
        program-agnostic data representations.  Returns the following:
        - platform_name: The name of the platform over which to send
          messages
        - sender_data: A platform-specific dictionary representing the
          sender
        - recipients_data: A list of platform-specific representations
          of recipients
        - content: The template for the content of the messages
        - templating_data: The full set of data used to fill the
          template
        - user_table_data: A list of users, where a user is a mapping
          of platform names to lists of usernames
        :param platform_name: The name of the platform over which to
        send messages
        :param sender_json: The platform-specific JSON data
        representing the sender
        :param recipients_text: A list of platform-specific textual
        representations of recipients
        :param content: The template for the content of the messages
        :param templating_data_json: JSON representing the full set of
        data used to fill the template
        :param user_table_yaml: YAML representing a list of users,
        where a user is a mapping of platform names to lists of
        usernames
        :return: A dictionary containing the key value pairs described
        above
        """
        user_table_data = yaml.load(user_table_yaml)
        templating_data = json.loads(templating_data_json)
        return {
            **super().agnostic_parse(platform_name,
                                     sender_json,
                                     recipients_text,
                                     content),
            'templating_data': templating_data,
            'user_table_data': user_table_data
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
        - content: The template for the content of the messages
        - templating_data: The full set of data used to fill the
          template
        - user_table_data: A list of users, where a user is a mapping
          of platform names to lists of usernames
        :return: A dictionary containing the key value pairs described
        above
        """
        args = self.parse_args()
        return self.agnostic_parse(**self.fill_in_args(args.platform,
                                                       args.sender,
                                                       args.recipients,
                                                       args.content,
                                                       args.data,
                                                       args.user_table))


def build_resources(platform_name,
                    sender_data,
                    recipients_data,
                    content,
                    templating_data,
                    user_table_data):
    """
    Parses program-agnostic data representations into
    platform-specific classes.  The resources are as follows:
    - platform: An instance of the `comm.platform.Platform`
      subclass corresponding to the given platform name
    - sender: An instance of the `comm.platform.ClientUser`
      subclass corresponding to the given platform name
    - recipients: A list of instances of the `comm.platform.User`
      subclass corresponding to the given platform name
    - content: The template for the content of the messages
    - templating_data: The full set of data used to fill the
      template
    - user_table: An instance of `comm.user_table.UserTable`
      wrapping the given user table data
    :param platform_name: The name of the platform over which to
    send messages
    :param sender_data: A platform-specific dictionary representing
    the sender
    :param recipients_data: A list of platform-specific
    representations of recipients
    :param content: The template for the content of the messages
    :param templating_data: The full set of data used to fill the
    template
    :param user_table_data: A list of users, where a user is a
    mapping of platform names to lists of usernames
    :return: A dictionary containing the key value pairs described
    above
    """
    user_table = UserTable(user_table_data)
    if recipients_data == []:
        logging.debug('No recipients specified in command line args. '
                      'Loading recipients from user table.')
        recipients_data = [*user_table.get_users(platform_name)]
    return {
        **basic.build_resources(platform_name,
                                sender_data,
                                recipients_data,
                                content),
        'templating_data': templating_data,
        'user_table': user_table
    }


def build_messages(platform,
                   sender,
                   recipients,
                   content,
                   templating_data,
                   user_table,
                   template_input_builder):
    """
    Produces a list of messages with the same sender.  The content is
    a template filled with personalized data for each recipient.
    No message will be produced for recipients with no corresponding
    data.
    :param platform: An instance of the `comm.platform.Platform`
    subclass corresponding to the platform over which the message will
    be sent
    :param sender: An instance of the `comm.platform.ClientUser`
    subclass corresponding to the platform over which the message will
    be sent
    :param recipients: A list of instances of the `comm.platform.User`
    subclass corresponding to the platform over which the message will
    be sent
    :param content: The template for the content of the messages
    :param templating_data: The full set of data used to fill the
    template
    :param user_table: An instance of `comm.user_table.UserTable`
    :param template_input_builder: A function that returns the strings
    used to fill the message content template with personalized
    information from provided data, or returns None if no relevant
    information is found
    :return: A list of `comm.basic.Message` objects
    """
    platform_name = platforms.platform_name[type(platform)]
    unfilled_messages = basic.build_messages(sender, recipients, content)
    messages = []
    for message in unfilled_messages:
        recipient_id = message.recipient.get_id()
        try:
            user = user_table.get_user(platform_name, recipient_id)
        except KeyError:
            logging.error('Skipping user \'{}\' because no user table entry '
                          'was found'.format(recipient_id))
            continue
        template_input = template_input_builder(user=user,
                                                data=templating_data)
        if template_input is None:
            continue
        try:
            content = message.content.format(*template_input)
        except TypeError as e:
            raise TypeError('Output of template_input_builder must be a '
                            'tuple.') from e
        messages.append(basic.Message(message.sender,
                                      message.recipient,
                                      content))
    return messages


def _send_to_all(platform,
                 sender,
                 recipients,
                 content,
                 templating_data,
                 user_table,
                 template_input_builder):
    """
    Requires instances of platform-specific classes; for internal use.
    """
    messages = build_messages(**locals())
    for message in messages:
        basic.send_message(message)


def send_to_all(platform_name,
                sender_data,
                recipients_data,
                content,
                templating_data,
                user_table_data,
                template_input_builder):
    """
    Formats a message template for a set of recipients with
    personalized information pulled from the given data, then sends
    the messages via the specified platform. Messages are only sent to
    recipients for which corresponding information can be found.
    :param platform_name: The name of the platform over which to send
    messages
    :param sender_data: A platform-specific dictionary representing
    the sender
    :param recipients_data: A list of platform-specific
    representations of recipients
    :param content: The template for the content of the messages
    :param templating_data: The full set of data used to fill the
    template
    :param user_table_data: A list of users, where a user is a mapping
    of platform names to lists of usernames
    :param template_input_builder: A function that returns the strings
    used to fill the message content template with personalized
    information from provided data, or returns None if no relevant
    information is found
    """
    _send_to_all(template_input_builder=template_input_builder,
                 **build_resources(platform_name,
                                   sender_data,
                                   recipients_data,
                                   content,
                                   templating_data,
                                   user_table_data))
