"""
Implement User, ClientUser, and Module for any additional platforms.
"""
from abc import ABCMeta, abstractmethod


class User(metaclass=ABCMeta):
    """
    A user of a communication platform, with a username that can be
    referenced by others for communicating with this user.
    """

    @abstractmethod
    def get_id(self):
        """
        Gets this user's primary identifier, such as an address or
        username.
        :return: The identifier
        """
        pass


class ClientUser(User, metaclass=ABCMeta):
    """
    A user of a communication platform, with an identifier that can be
    used by others for communicating with this user, and the ability
    to send messages to other users.
    """

    @abstractmethod
    def send_message(self, recipient, content):
        """
        Sends a message from this User to another.
        :param recipient: the recipient of the message
        :param content: the content of the message
        """
        pass


class Platform(metaclass=ABCMeta):
    """
    An adaptor for the instantiation of platform-specific User and
    ClientUser subclasses.
    """

    @abstractmethod
    def build_sender(self, data):
        """
        Creates a sender from the given data.
        :param data: the data used to create the sender
        :return: the sender
        """
        pass

    @abstractmethod
    def build_recipient(self, data):
        """
        Creates a recipient from the given data.
        :param data: the data used to create the recipient
        :return: the recipient
        """
        pass
