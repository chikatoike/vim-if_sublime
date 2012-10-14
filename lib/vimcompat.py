# Compatibility layer for if_python and Sublime Text 2 Packages.
import os
import glob
import logging
import sublime_plugin

debug = False
evalenv = {}

try:
    import vim
    enable_vim = True
except ImportError:
    enable_vim = False

def create_compat():
    if enable_vim:
        return VimCompat()
    else:
        return DummyCompat()

class DummyObject(object):
    pass


# Interface for Vim {{{1
def setvimenv(env):
    def builtin_p(val):
        return isinstance(val, int) or isinstance(val, str)
    env = { key: val for key, val in env.items() if builtin_p(val) }

    global evalenv
    evalenv = env

    vim.command('python import vimcompat')
    vim.command('unlet! g:sublimenv')
    vim.command('let g:sublimenv = pyeval("vimcompat.evalenv")')

def vimeval(expr, env={}):
    setvimenv(env.copy())
    return vim.eval(expr)

def vimcommand(expr, env={}):
    setvimenv(env.copy())
    return vim.command(expr)


class VimWindow(object):
    def __init__(self, window):
        self.window = window

    @property
    def buffer(self):
        return VimBuffer(self.window.buffer)

    @property
    def cursor(self):
        return self.window.cursor

    @property
    def height(self):
        return self.window.height


class VimBuffer(object):
    def __init__(self, buffer):
        self.buffer = buffer

    def __getitem__(self, key):
        encoding = compat.getbufferencoding(self.buffer.name)
        if isinstance(key, slice):
            data = eval('self.buffer[%s : %s]' % (
                key.start if not key.start is None else '',
                key.stop if not key.stop is None else ''
                ))
            return [unicode(s, encoding) for s in data]
        else:
            return unicode(self.buffer[key], encoding)

    def __setitem__(self, key, value):
        encoding = compat.getbufferencoding(self.buffer.name)
        if isinstance(key, slice):
            data = [s.encode(encoding) for s in value]
            eval('self.buffer[%s : %s] = data' % (
                key.start if not key.start is None else '',
                key.stop if not key.stop is None else ''
                ))
        else:
            self.buffer[key] = data.encode(encoding)

    @property
    def name(self):
        return self.buffer.name

    # TODO implement other attributes.


class VimCompat(object):
    def __init__(self):
        self.vim = DummyObject()
        self.vim.eval = vimeval
        self.vim.command = vimcommand

    def message(self, string):
        self.vim.command('echomsg g:sublimenv.string', locals())

    def trace(self, string):
        if debug:
            # string = string if isinstance(string, str) else str(string)
            self.vim.command('echomsg "sublime:" g:sublimenv.string', locals())

    def getvimwindow(self, winnr=-1):
        if winnr == -1:
            return VimWindow(vim.current.window)
        else:
            return VimWindow(vim.windows[winnr - 1])

    def getbufvar(self, path, option):
        return self.vim.eval('getbufvar(g:sublimenv.path, g:sublimenv.option)', locals())

    def setbufvar(self, path, option, value):
        self.vim.eval('setbufvar(g:sublimenv.path, g:sublimenv.option, g:sublimenv.value)', locals())

    # def getbufvarbool(self, path, option):
    #     return self.vim.eval('getbufvar(g:sublimenv.path, g:sublimenv.option)', locals()) != '0'

    def getfiletype(self, path):
        self.trace('VimCompat.getfiletype: ' + path)
        return self.vim.eval('get(g:vimsublime_filetype, getbufvar(g:sublimenv.path, "&filetype"), "")', locals())

    def getbufferencoding(self, path):
        encoding = compat.getbufvar(path, '&fileencoding')
        if encoding == '':
            encoding = compat.getbufvar(path, '&encoding')
        return encoding

    def globpath(self, pattern):
        return DummyCompat().globpath(pattern)
        # return self.vim.eval(
        #         'split(globpath(&runtimepath, g:sublimenv.pattern), "\\n")', locals())

    def open_file(self, path, line=0, col=0):
        if line == 0:
            self.vim.command('edit `=g:sublimenv.path`', locals())
        else:
            self.vim.command('edit +%d `=g:sublimenv.path`' % (line,), locals())
            self.vim.command('call cursor(g:sublimenv.line, g:sublimenv.col + 1)', locals())


# Dummy interface {{{1
class DummyCompat(VimCompat):
    def __init__(self):
        self.windows = [DummyWindow(os.path.dirname(__file__) + '/../test/test.cpp')]
        self.current = DummyObject()
        self.current.window = self.windows[0]
        self.current.buffer = self.current.window.buffer

    def message(self, string):
        print(string)

    def trace(self, string):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.debug(string)

    def getvimwindow(self, winnr=-1):
        if winnr == -1:
            return self.current.window
        else:
            return self.windows[winnr - 1]

    def getbufvar(self, path, option):
        return self.current.buffer.bufvar.get(option, '')

    def setbufvar(self, path, option, value):
        self.current.buffer.bufvar[option] = value

    def getfiletype(self, path):
        return 'c++'

    def globpath(self, pattern):
        dir = os.path.dirname(__file__)
        return glob.glob(os.path.join(dir, pattern))

    def open_file(self, path, line=0, col=0):
        self.windows[0] = DummyWindow(path)
        self.current.window.buffer = self.windows[0].buffer
        self.current.window.cursor = (line, col)
        self.current.buffer = self.current.window.buffer

class DummyWindow(object):
    def __init__(self, path):
        self.buffer = DummyBuffer(path)
        # line is 1 based.
        # self.cursor = (12, 5)
        self.cursor = (13, 3)

class DummyBuffer(object):
    def __init__(self, path):
        self.name = os.path.normpath(path)
        with open(self.name, 'r') as f:
            self.text = f.read().split("\n")
            self.text = [unicode(line, 'utf-8') for line in self.text]
        self.bufvar = {}

    def __getitem__(self, key):
        return self.text[key]


# Instances {{{1
compat = create_compat()

# Sublime Text 2 builtin commands {{{1
class DummyCommand(object):
    def __init__(self, extra=None):
        # compat.trace('DummyCommand.__init__')
        pass

    def run(self, extra=None):
        compat.trace('DummyCommand:')
        # compat.trace('DummyCommand:' + getcallerinfo())

class SublimeDummyAutoComplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # if debug:
        #     return [('aaa', 'aaa(bbb)')]
        return []

class HideAutoComplete(DummyCommand, sublime_plugin.TextCommand):
    def __init__(self, view):
        super(HideAutoComplete, self).__init__(view)
    def run(self, edit):
        # TODO
        pass

class AutoComplete(DummyCommand, sublime_plugin.TextCommand):
    def __init__(self, view):
        super(AutoComplete, self).__init__(view)
        self.view = view
    def run(self, edit):
        raise NotImplementedError
#         view = self.view
#         locations = [view.sel()[0].a]
# 
#         # TODO What's prefix?
#         completions, flags = sublime.on_query_completions('', locations, view)
#         compat.trace('AutoComplete: completion list:')
#         for compl in completions:
#             compat.trace('AutoComplete: ' + repr(compl[1]))

