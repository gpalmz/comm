import smtplib

from comm.platform import User, ClientUser, Platform


class EmailUser(User):

    def __init__(self, address):
        self.address = address

    def get_id(self):
        return self.address


class EmailClientUser(ClientUser, EmailUser):

    def __init__(self, server, address, password):
        super().__init__(address)
        self.password = password
        self.server = server
        self.server.starttls()
        self.server.login(self.address, self.password)

    def __del__(self):
        try:
            self.server.quit()
        except smtplib.SMTPServerDisconnected:
            pass

    def send_message(self, recipient, content):
        self.server.sendmail(self.address, recipient.address, content)


class Email(Platform):

    def __init__(self):
        self._servers = {}

    def build_sender(self, data):
        domain = data['address'].split('@')[1]
        if domain in self._servers:
            server = self._servers[domain]
        else:
            server = smtplib.SMTP(**data['smtp'])
            self._servers[domain] = server
        return EmailClientUser(server, data['address'], data['password'])

    def build_recipient(self, data):
        if not isinstance(data, dict):
            data = {'address': data}
        return EmailUser(**data)
