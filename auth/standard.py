#none yet!
class Credentials:
    """
    Class representing a voter's credentials.
    """
    def __init__(self, user_id=None, friendly_name=None, groups=None):
        if user_id == None:
            raise TypeError, "missing argument 'user_id'"
        elif friendly_name == None:
            raise TypeError, "missing argument 'friendly_name'"
        elif groups == None:
            raise TypeError, "missing argument 'groups'"

        else:
            self.user_id = user_id
            self.friendly_name = friendly_name
            self.groups = groups

    def in_group(self, group):
        return self.groups.count(group) > 0

class BaseAuth:
    pass
