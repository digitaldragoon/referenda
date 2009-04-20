from referenda.auth.standard import *
import ldap
import os

class UpsGeneralAuth (BaseAuth):
    LDAP_SERVER="dm-2.pugetsound.edu"
    necessary_groups = []
    blocked_groups = []

    def _ldap_bind(self):
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '%s/dm3.pem' % os.path.dirname(__file__))
        con = ldap.initialize("ldaps://%s" % self.LDAP_SERVER)
        con.simple_bind_s('LDAP Authenticator', 'Sspr609z')
        return con

    def _ldap_search(self, con, user_id, ret):
        base = "dc=pugetsound,dc=edu"
        scope = ldap.SCOPE_SUBTREE
        filter = "(SAMAccountName=" + user_id + ")"

        result_id = con.search(base, scope, filter, ret)
        result_type, result_data = con.result(result_id, 0)

        return result_data[0][1]

    def _get_groups(self, con, user_id):
        # compile groups
        ret = ['memberOf']
        list = self._ldap_search(con, user_id, ret)['memberOf']
        groups = []

        for string in list:
            spl = string.split(',')
            groups.append(spl[0].split('=')[1])

        return groups

    def authenticate(self, user_id, password):
        """
        Takes a user_id and password and returns a tuple. The first element is a boolean declaring whether the credentials were correct, and the second is the list of groups to which that account belongs.
        """
        if user_id == '' or user_id == None:
            return None

        full_id = 'PUGETSOUND\%s' % user_id

        try:
            con = self._ldap_bind()
            con.simple_bind_s(full_id, password)

        except ldap.INVALID_CREDENTIALS:
            raise InvalidCredentials

        else:
            try:
                # get friendly name
                ret = ['givenName']
                friendly_name = self._ldap_search(con, user_id, ret)['givenName'][0]

                groups = self._get_groups(con, user_id)

                con.unbind()

                # validate user is in necessary groups
                valid_groups = True
                for group in self.necessary_groups:
                    valid_groups = valid_groups and groups.count(group) > 0

                for group in self.blocked_groups:
                    valid_groups = valid_groups and not groups.count(group) > 0

                if valid_groups:
                    return Credentials(user_id, friendly_name, groups)
                else:
                    raise Unauthorized
            except ldap.OPERATIONS_ERROR:
                raise InvalidCredentials

class UpsStudentAuth (UpsGeneralAuth):
    necessary_groups = ['StudentAccts',]
    blocked_groups = ['OutgoingStudent',]
    message = 'You must be a UPS student to vote.'

    def _get_groups(self, con, user_id):
        import csv
        import os

        CY_TABLE = {
            '1': 'Freshman',
            '2': 'Sophomore',
            '3': 'Junior',
            '4': 'Senior',
        }

        RT_TABLE = {
            'R': 'ResidenceHall',
            'G': 'Greek',
            'H': 'OnCampusHouse',
            'N': 'OffCampusHouse',
        }
        
        reader = csv.reader(open(os.path.dirname(__file__) + '/student_voting_eligibility.csv', "rb"))

        groups = []
        for row in reader:
            if row[0].lower() == user_id:
                groups.append(CY_TABLE[row[1][0]])
                groups.append(RT_TABLE[row[1][1]])

        return groups + super(UpsStudentAuth, self)._get_groups(con, user_id)

class UpsFacultyAuth (UpsGeneralAuth):
    message = 'You must be a UPS faculty member to vote.'

    def authenticate(self, user_id, password):
        file = open(os.path.dirname(__file__) + '/faculty_list_2009', "rb")

        for line in file:
            id = line.strip('\n')
            
            if user_id.lower() == id.lower():
                return super(UpsFacultyAuth, self).authenticate(user_id, password)

        raise Unauthorized
