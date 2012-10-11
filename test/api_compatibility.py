import sys
import os
import platform as platform_


def source(name):
    return os.path.normpath(os.path.dirname(__file__) + '/' + name)

def test_sublime_module():
    """
    >>> import sublime
    >>> from api_compatibility import *
    >>> #s = sublime.load_settings('api_compatibility.sublime-settings')
    >>> #s['api_compatibility_test1'] True
    >>> #s['api_compatibility_test2'] [1, 2, 3]
    >>> # sublime.version()
    >>> sublime.packages_path() == unicode(os.path.expandvars('$APPDATA\\Sublime Text 2\\Packages')) or platform_.system() != 'Windows'
    True
    >>> sublime.packages_path() == unicode(os.path.expandvars('$HOME/Library/Application Support/Sublime Text 2/Packages')) or platform_.system() != 'osx'
    True
    >>> sublime.packages_path() == unicode(os.path.expandvars('$HOME/.config/sublime-text-2/Packages')) or platform_.system() != 'Linux'
    True
    >>> sublime.platform() == u'windows' or platform_.system() != 'Windows'
    True
    >>> sublime.platform() == u'osx' or platform_.system() != 'osx'
    True
    >>> sublime.platform() == u'linux' or platform_.system() != 'Linux'
    True
    >>> sublime.arch() == u'x86' or platform_.machine() != 'x86'
    True
    """

def test_view():
    """
    >>> from sublime import *
    >>> from api_compatibility import *
    >>> a = active_window().open_file(source('test.cpp'))
    >>> view = active_window().active_view()
    >>> view.rowcol(0)
    (0, 0)

    """
    pass

try:
    from sublime import *
    # print('Running on fake API with Vim.')

except ImportError:
    sys.path += [os.path.normpath(os.path.dirname(__file__) + '/../if_sublime')]
    from sublime import *
    # print('Running on stand alone fake API.')
    import vimcompat
    vimcompat.debug = True

if __name__ == '__main__':
    import doctest
    doctest.testmod()
