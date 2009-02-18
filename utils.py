from referenda.auth.standard import BaseAuth
import os
import inspect

def get_authenticators():
    """
    Gets a list of all fully-qualified class names in the auth directory.
    """
    files = os.listdir(os.path.abspath(os.path.dirname(__file__) + '/auth'))
    module_names = []

    for f in files:
        filename, ext = os.path.splitext(f)
        if ext == '.py':
            module_names.append(filename)

    authenticators = []

    for module_name in module_names:
        try:
            mod = __import__('referenda.auth.%s' % module_name, {}, {}, [module_name,])
        except ImportError:
            raise ImportError, 'error importing Referenda authenticators'

        else:
            for name in dir(mod):
                item = getattr(mod, name)
                if inspect.isclass(item) and issubclass(item, BaseAuth) and item.__name__ != 'BaseAuth':
                    authenticators.append('referenda.auth.%s.%s' % (module_name, name))

    return authenticators

def get_auth_choices():
    """
    Wraps the results from get_authenticators into a tuple of tuples suitable for including in a model field's "choices" argument.
    """
    authenticators = get_authenticators()
    auth_list = []

    for auth in authenticators:
        auth_list.append((auth, auth.rsplit('.', 1)[1]))

    return tuple(auth_list)
