from slacker import Slacker

from comm.platform import User, ClientUser, Platform


class SlackUser(User):

    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username


class SlackClientUser(ClientUser, SlackUser):

    def __init__(self, username, token):
        super().__init__(username)
        self.token = token
        self.slacker = Slacker(self.token)

    def send_message(self, recipient, content):
        self.slacker.chat.post_message(
            recipient.username,
            content,
            as_user=True
        )


class Slack(Platform):

    def build_sender(self, data):
        return SlackClientUser(**data)

    def build_recipient(self, data):
        if not isinstance(data, dict):
            data = {'username': data}
        return SlackUser(**data)
