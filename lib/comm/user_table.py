class User(dict):
    """
    An entry containing lists of associated identifiers by platform.
    """

    def get_ids(self, platform):
        """
        Gets this user's identifiers for the specified platform.
        :param platform: The name of the platform as seen in the user
        table
        :return: A list of identifiers
        """
        return self[platform]


class UserTable(list):
    """
    A list of users, where each user is a mapping of platform names to
    lists of identifiers for that platform.
    """

    def __init__(self, data):
        super().__init__(data)
        self.mappings = self._build_mappings()

    def _build_mappings(self):
        platform_map = {}
        for user in self:
            user = User(user)
            for platform in user:
                if platform not in platform_map:
                    platform_map[platform] = {}
                id_map = platform_map[platform]
                for user_id in user.get_ids(platform):
                    id_map[user_id] = user
        return platform_map

    def get_users(self, platform):
        """
        Gets a mapping of identifiers to users for all identifiers
        registered for the given platform.
        :param platform: The platform to get users for
        :return: The mapping of identifiers to users
        """
        return self.mappings[platform]

    def get_user(self, platform, username):
        """
        Gets a user based on a platform and username.
        :param platform: The platform for which the username is
        registered
        :param username: The username
        :return: The user
        """
        return self.get_users(platform)[username]

    def get_unrecognized(self, platform, usernames):
        """
        Produces a list of any unrecognized usernames from the given
        list for the given platform.
        :param platform: The platform for which to search usernames
        :param usernames: The usernames to filter from
        :return: A list of unrecognized usernames
        """
        return [username
                for username in usernames
                if username not in self.get_users(platform)]
