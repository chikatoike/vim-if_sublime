# Imitation of Sublime Text 2 API.
# Reference: http://www.sublimetext.com/docs/2/api_reference.html
import sys
import imp
import os
import re
import glob
import json
import platform as platform_
import sublime_plugin
import vimcompat

# constant values
ENCODED_POSITION = 0x01
TRANSIENT = 0x02

# ???
INHIBIT_WORD_COMPLETIONS = 0x01
INHIBIT_EXPLICIT_COMPLETIONS = 0x02


# sublime module {{{1
def load_settings(setting_filename):
    return Settings(setting_filename)

def status_message(string):
    compat.message('status_message: ' + string)

def set_timeout(callback, delay):
    """
    This function can be called from different thread.
    TODO Make thread safe.
    """
    deferred.register(Callback(callback, delay))

def active_window():
    """ TODO Returns current tabpage. """
    return _window

def get_clipboard():
    raise NotImplementedError

def set_clipboard(string):
    raise NotImplementedError

def scope_selector(scope, selector):
    raise NotImplementedError


# sublime module (platform) {{{1
_osname = (
    u'windows' if platform_.system() == 'Windows' else
    u'osx' if platform_.system() == 'osx' else
    u'linux' if platform_.system() == 'Linux' else
    u'')

_sublime_data_path = os.path.expandvars(
    ur'$APPDATA\Sublime Text 2' if platform_.system() == 'Windows' else
    ur'$HOME/Library/Application Support/Sublime Text 2' if platform_.system() == 'osx' else
    ur'$HOME/.config/sublime-text-2' if platform_.system() == 'Linux' else
    ur'')

def packages_path():
    return os.path.join(_sublime_data_path, 'Packages')

def installed_packages_path():
    return os.path.join(_sublime_data_path, 'Installed Packages')

def version():
    return u'2000'

def platform():
    return _osname

def arch():
    return u'x32' if platform_.machine() == 'x86' else u'x64'


# Deferred {{{1
class Deferred(object):
    def __init__(self):
        self.lst = []

    def register(self, callback):
        self.lst.append(callback)

    def notify_all(self):
        for callback in self.lst:
            compat.message('timeout callback: ' + str(callback.func))
            callback.func()
        self.lst = []

    def check(self):
        # TODO check timeout
        pass

class Callback(object):
    def __init__(self, func, delay):
        self.func = func
        self.delay = delay

# glob {{{1
def _glob(base_name_pattern):
    files = []
    for path in plugin_path:
        files += glob.glob(os.path.join(path, base_name_pattern))

    files += glob.glob(os.path.join(packages_path(), 'User', base_name_pattern))

    vim_plugin = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../plugin/if_sublime')
    files += glob.glob(os.path.join(vim_plugin, base_name_pattern))
    return files

# Plugin interface {{{1
plugin_path = []

def add_path(package_path):
    global plugin_path
    plugin_path +=  package_path
    plugin_path = [x for i,x in enumerate(plugin_path) if plugin_path.index(x) == i]

def load_plugin(package_path):
    add_path(package_path)

    if not '.' in sys.path:
        sys.path.append('.')

    prev_dir = os.getcwd()

    for path in package_path:
        os.chdir(path)
        plugins = glob.glob('*.py')
        for fname in plugins:
            source_plugin(fname)
        # modulename = os.path.basename(path).lower()
        # source_plugin(os.path.join(path, modulename + '.py'))

    os.chdir(prev_dir)

def source_plugin(fname):
    modulename, _ = os.path.splitext(os.path.basename(fname))
    if modulename in sys.modules:
        return
    imp.load_source(modulename, fname)

def run_window_command(command_name, args={}):
    _window.run_command(command_name, args)

def run_text_command(command_name, args={}):
    _window.active_view().run_command(command_name, args)

def run_command(command_name, args={}):
    """
    Runs the named ApplicationCommand.
    """
    try:
        plugin = _find_command(command_name, sublime_plugin.ApplicationCommand.__subclasses__())
        command = plugin()
        if args:
            command.run(**args)
        else:
            command.run()
    finally:
        pass

def _find_command(plugin_name, commands):
    """
    Searches command class using conventions for command names.
    http://docs.sublimetext.info/en/latest/reference/plugins.html#conventions-for-command-names
    """
    name = _camelize(plugin_name)
    for plugin in commands:
        if plugin.__name__ == name or plugin.__name__ ==  (name + 'Command'):
            return plugin
    raise Exception("Command not found: " + repr(name) + " : " + repr(plugin_name))

def _camelize(str):
    p = re.compile(r'(^|_)([a-z])')
    return p.sub((lambda match: match.groups(0)[1].upper()), str)

# EventListener {{{1
def on_new(view=None): _call_event_listeners(view, 'on_new')
def on_clone(view=None): _call_event_listeners(view, 'on_clone')
def on_load(view=None): _call_event_listeners(view, 'on_load')
def on_close(view=None): _call_event_listeners(view, 'on_close')
def on_pre_save(view=None): _call_event_listeners(view, 'on_pre_save')
def on_post_save(view=None): _call_event_listeners(view, 'on_post_save')
def on_modified(view=None): _call_event_listeners(view, 'on_modified')
def on_selection_modified(view=None): _call_event_listeners(view, 'on_selection_modified')
def on_activated(view=None): _call_event_listeners(view, 'on_activated')
def on_deactivated(view=None): _call_event_listeners(view, 'on_deactivated')
# def on_query_context(view=None): pass

def on_query_completions(line=-1, col=-1, prefix='', view=None):
    view = view if not view is None else _window.active_view()

    if line < 0 or  col < 0:
        locations = [view.sel()[0].a]
    else:
        locations = [view.text_point(line - 1, col)]

    line = view.substr(view.line(locations[0]))
    compat.trace('on_query_completions: prefix: ' + repr(prefix))
    compat.trace('on_query_completions: location: ' + repr(line))
    compat.trace('on_query_completions:           ' + (' ' * len(repr(line[: view.rowcol(locations[0])[1]]))) + '^')

    completions = []
    flags = 0
    for handler in _get_event_listeners('on_query_completions'):
        res = handler(view, prefix, locations)

        if isinstance(res, tuple):
            completions += res[0]
            flags |= res[1]
        elif isinstance(res, list):
            completions += res

    # compat.trace('on_query_completions: ' + repr((completions, flags)))
    return (completions, flags)

def _get_event_listeners(event_name):
    for plugin in sublime_plugin.EventListener.__subclasses__():
        event_listener = plugin()
        handler = getattr(event_listener, event_name)
        if not handler is None:
            compat.trace('Found EventListener ' + str(event_listener))
            yield handler

def _call_event_listeners(view, event_name):
    view = view if not view is None else _window.active_view()

    # TODO create event listener instances once
    try:
        for plugin in sublime_plugin.EventListener.__subclasses__():
            event_listener = plugin()
            handler = getattr(event_listener, event_name)
            if not handler is None:
                handler()
    finally:
        pass

# Settings {{{1
class Settings(object):
    """
    NOTE it is not subscriptable.
    """
    def __init__(self, setting_filename=None):
        if not setting_filename is None:
            self.settings = Settings._load(setting_filename)
        else:
            self.settings = {}

    def get(self, name, default=None):
        if name in self.settings:
            return self.settings[name]
        elif not default is None:
            return default
        else:
            # TODO raise DataError()
            return None

    def set(self, name, value):
        self.settings[name] = value

    def erase(self, name):
        del self.settings[name]

    def has(self, name):
        return name in self.settings

    def add_on_change(self, key, on_change):
        pass # TODO

    def clear_on_change(self, key):
        pass # TODO

    @staticmethod
    def _load(setting_filename):
        """ required path relative to package's root directory.
        >>> s = Settings._load('SublimeClang.sublime-settings')
        >>> s.get('warm_up_in_separate_thread')
        False
        >>> s.get('debug_options')
        True
        """
        d = {}
        for path in _glob(setting_filename):
            # compat.trace('Settings._load: ' + path)
            with open(path, 'r') as f:
                text = f.read()
                # TODO remove block style comments
                text = re.sub(r'//.*', '', text) # remove line comments.
                try:
                    d.update(json.loads(text))
                except ValueError:
                    compat.trace('Settings._load: invalid json file: ' + path)
                    raise
        return d

# Edit {{{1
class Edit(object):
    pass


# Window {{{1
class Window(object):
    def __init__(self):
        self.panels = {}

    def run_command(self, command_name, args={}):
        """
        Runs the named WindowCommand.
        """
        try:
            plugin = _find_command(command_name, sublime_plugin.WindowCommand.__subclasses__())
            command = plugin(self)
            if args:
                command.run(**args)
            else:
                command.run()
        finally:
            pass

    def active_view(self):
        return View()

    def open_file(self, target, flags=None):
        """
        NOTE TRANSIENT is never used.
        """
        if not flags is None and (flags & ENCODED_POSITION) != 0:
            compat.trace('Window.open_file: ' + target)
            m = re.match(r'^(.*):(\d+):(\d+)$', target)
            if m:
                path, line, col = m.groups()
                compat.open_file(path, int(line), int(col))
            else:
                # TODO ignore line, col
                compat.open_file(target)
        else:
            compat.open_file(target)
        return self.active_view()

    def show_quick_panel(self, items, on_done, flags=None):
        # TODO inputlist() or unite.vim
        compat.trace('Window.show_quick_panel: ' + repr(items))
        on_done(0)

    def folders(self):
        if not vimcompat.enable_vim:
            # FIXME it will crash
            return [os.getcwd()]
        else:
            return []

    def get_output_panel(self, name):
        if name in self.panels:
            return self.panels[name]
        else:
            return Panel(name)

# View {{{1
class View(object):
    def __init__(self):
        self.vimwin = compat.getvimwindow()
        self.status = {}
        self._settings = Settings()

    def settings(self):
        return self._settings

    def run_command(self, command_name, args={}):
        """
        Runs the named TextCommand.
        """
        try:
            plugin = _find_command(command_name, sublime_plugin.TextCommand.__subclasses__())
            command = plugin(self)
            if args:
                edit = self.begin_edit(command_name, args)
                command.run(edit, **args)
            else:
                edit = self.begin_edit(command_name)
                command.run(edit)
        finally:
            self.end_edit(edit)

    def file_name(self):
        return self.vimwin.buffer.name

    def scope_name(self, point):
        # language_regex = re.compile("(?<=source\.)[\w+#]+")
        # scope_name used for language detection?
        return 'source.' + compat.getfiletype(self.vimwin.buffer.name)

    def window(self):
        return _window

    def is_dirty(self):
        return compat.getbufvar(self.vimwin.buffer.name, '&modified') == '1'

    def is_scratch(self):
        return compat.getbufvar(self.vimwin.buffer.name, '&buftype') != ''

    def set_scratch(self, value):
        compat.setbufvar(self.vimwin.buffer.name, '&buftype', 'nofile' if value else '')

    def is_read_only(self):
        return compat.getbufvar(self.vimwin.buffer.name, '&readonly') == '1'

    def set_read_only(self, value):
        compat.setbufvar(self.vimwin.buffer.name, '&readonly', 1 if value else 0)

    def set_syntax_file(self, syntax_file):
        # TODO
        pass

    def sel(self):
        """
        Returns current cursor point or selection. (Zero based)
        """
        # vimwin.cursor[0]: line is 1 based.
        # vimwin.cursor[1]: col is zero based.
        cursor = self.vimwin.cursor
        return RegionSet(Region(self.text_point(cursor[0] - 1, cursor[1])), self)

    def begin_edit(self, command=None, args={}):
        # Returns edit object.
        return {}

    def end_edit(self, edit):
        pass

    def rowcol(self, point):
        if isinstance(point, Point):
            return point.get(self)
        elif isinstance(point, int):
            return self._get_rowcol(point)

    def text_point(self, row, col):
        return Point(row, col, len(self._substr_pos(row, col)))

    def _point_min(self):
        """
        This is not standard API.
        """
        return Point.fromint(0)

    def _point_max(self):
        """
        This is not standard API.
        """
        raise NotImplementedError

    def _substr_pos(self, line, col):
        """
        >>> view = _test_view()
        >>> view._substr_pos(0, 0)
        u''
        """
        lines = self.vimwin.buffer[: line]
        last = self.vimwin.buffer[line][: col]
        return '\n'.join(lines + [last])

    def _get_rowcol(self, point):
        i = 0
        row = 0
        for line in self.vimwin.buffer:
            llen = len(line) + 1
            if point < (i + llen):
                return (row, point - i)
            i += llen
            row += 1
        raise Exception('View._get_rowcol: point is out of range.')

    def size(self):
        return len('\n'.join(self.vimwin.buffer[:]))

    def insert(self, edit, point, string):
        compat.trace('View.insert: ' + str(point) + ' ' + string)

    def erase(self, edit, region):
        # TODO
        pass

    def replace(self, edit, region, string):
        # TODO
        pass

    def substr(self, point):
        if isinstance(point, Point):
            line, col = self.rowcol(point)
            compat.trace('View.substr: point: ' + repr(self.vimwin.buffer[line][col]))
            # TODO contains eol char?
            return self.vimwin.buffer[line][col]
        elif isinstance(point, Region):
            region = point
            begin_line, begin_col = self.rowcol(region.begin())
            end_line, end_col = self.rowcol(region.end())
            lines = self.vimwin.buffer[begin_line : end_line + 1] # end line is contains last line.
            if len(lines) == 1:
                lines[0] = lines[0][begin_col : end_col]
            else:
                lines[0] = lines[0][begin_col :]
                lines[-1] = lines[-1][: end_col] # end col is not contains last char
            # if len(lines) <= 1:
            #     compat.trace('View.substr: region: ' + repr('\n'.join(lines)))
            return '\n'.join(lines)

    def line(self, point):
        # args is point or region
        if isinstance(point, Point):
            line, _ = self.rowcol(point)
            end = len(self.vimwin.buffer[line])
            return Region(self.text_point(line, 0), self.text_point(line, end))
        elif isinstance(point, Region):
            region = point
            # TODO
            return self.line(region.a)

    def full_line(self, point):
        # args is point or region
        if isinstance(point, Point):
            line, _ = self.rowcol(point)
            end = len(self.vimwin.buffer[line])
            return Region(self.text_point(line, 0), self.text_point(line, end + 1))
        elif isinstance(point, Region):
            region = point
            # TODO
            return self.full_line(region.a)

    def word(self, point):
        # args is point or region
        if isinstance(point, Point):
            line, col = self.rowcol(point)
            rng = self._get_match_pos(r'\w+', self.substr(self.line(point)), col)
            if rng is None:
                return Region(self.text_point(line, col))
            return Region(self.text_point(line, rng[0]), self.text_point(line, rng[1]))
        elif isinstance(point, Region):
            raise NotImplementedError

    def _get_match_pos(self, pattern, text, current_col):
        """
        >>> view = _test_view()
        >>> view._get_match_pos(r'\w+', 'def aaa(arg):', 0)
        (0, 3)
        >>> view._get_match_pos(r'\w+', '\\tdef aaa(arg):', 6)
        (5, 8)
        >>> view._get_match_pos(r'\w+', '\\tt.member1 = 1;', 4)
        (3, 10)
        >>> view.word(view.text_point(12, 4)).get(view)
        ((12, 3), (12, 10))
        """
        for m in re.finditer(pattern, text):
            if m.start() <= current_col <= m.end():
                return (m.start(), m.end())
        return None

    # TODO regions {{{2
    def add_regions(self, key, regions, scope, icon=None, flags=None):
        pass

    def get_regions(self, key):
        return []

    def erase_regions(self, key):
        pass

    # status {{{2
    # TODO show status
    def set_status(self, key, value):
        compat.trace('View.set_status: ' + repr({key: value}))
        self.status[key] = value

    def get_status(self, key):
        return self.status[key]

    def erase_status(self, key):
        if key in self.status:
            self.status.pop(key)
        else:
            compat.trace('View.erase_status: not found key: ' + repr(key))


class Panel(View):
    def __init__(self, name):
        super(Panel, self).__init__()
        self.name = name


# Geometry {{{1
class RegionSet(object):
    """
    Set of regions. none overlap and sorted.
    RegionSet have a region or no region.
    NOTE Vim cannot have multiple regions.
    """
    def __init__(self, region, view):
        self.regions = [region]
        self.view = view

    def __getitem__(self, key):
        return self.regions[key]

    def __iter__(self):
        """
        >>> view = _test_view()
        >>> r = Region(view.text_point(0, 0), view.text_point(0, 1))
        >>> [i for i in RegionSet(r, view)][0].begin().get(view)
        (0, 0)
        """
        return (i for i in  self.regions)

    def clear(self):
        raise NotImplementedError
    def add(self, region):
        raise NotImplementedError
    def add_all(self, region_set):
        raise NotImplementedError
    def subtract(self, region):
        raise NotImplementedError
    def contains(self, region):
        raise NotImplementedError

class Region(object):
    """
    Region is same as vim's visual mode selection.
    NOTE Vim cannot have multiple regions.
    """
    def __init__(self, a, b=None):
        """
        a is the first end of region and point of cursor.
        b is the second end of region.
        If a equals b, there is not selection.
        NOTE end point contains last char
        """
        self.a = a if isinstance(a, Point) else Point.fromint(a)
        if b is None:
            self.b = self.a
        else:
            self.b = b if isinstance(b, Point) else Point.fromint(b)

    def __str__(self):
        return 'Region(%s, %s)' % (self.a, self.b)

    def __cmp__(self, other):
        if self.a != other.a:
            return self.a.__cmp__(other.a)
        else:
            return self.b.__cmp__(other.b)

    def begin(self):
        """
        >>> view = _test_view()
        >>> r = Region(view.text_point(0, 0), view.text_point(0, 1))
        >>> r.begin().get(view)
        (0, 0)
        """
        return min(self.a, self.b)

    def end(self):
        """
        >>> view = _test_view()
        >>> r = Region(view.text_point(0, 0), view.text_point(0, 1))
        >>> r.end().get(view)
        (0, 1)
        >>> r = Region(0, 1)
        >>> r.end().get(view)
        (0, 1)
        """
        return max(self.a, self.b)

    def get(self, view):
        return (self.a.get(view), self.b.get(view))


class Point(object):
    """
    This class is not exist in SublimeText API.
    In SublimeText, `point` is int. int value is offset of start of buffer.
    In this implementation,
    point is formed by tuple of line and column.
    NOTE line and col are zero based.
    NOTE line and col is never used. it is just a hint.
    NOTE offset type may be long but not int.
    """
    def __init__(self, line, col, offset):
        self._line = line
        self._col = col
        self._offset = offset

    def __str__(self):
        return 'Point(%d, %d)' % (self._line, self._col)

    def __cmp__(self, other):
        if isinstance(other, Point):
            return self._offset - other._offset
        elif isinstance(other, int):
            return self._offset - other
        else:
            raise NotImplementedError

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point.fromint(self._offset - other._offset)
        elif isinstance(other, int):
            return Point.fromint(self._offset - other)
        else:
            raise NotImplementedError

    def get(self, view):
        return view._get_rowcol(self._offset)

    @staticmethod
    def fromint(offset):
        return Point(-1, -1, offset)


# Instances {{{1
compat = vimcompat.create_compat()
deferred = Deferred()
_window = Window()


# test {{{1
def src(name):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test', name))

def _test_view():
    return active_window().open_file(src('test.cpp'))

if __name__ == "__main__":
    vimcompat.debug = True
    import doctest
    doctest.testmod(report=True)
    import unittest
    unittest.TextTestRunner().run(doctest.DocFileSuite(src('api_compatibility.txt')))
