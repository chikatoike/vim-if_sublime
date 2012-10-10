# Imitation of Sublime Text 2 API.
# Reference: http://www.sublimetext.com/docs/2/api_reference.html
import sys
import imp
import os
import re
import glob
import json
import sublime_plugin
import vimcompat

# constant values
ENCODED_POSITION = 0x01
TRANSIENT = 0x02

# ???
INHIBIT_WORD_COMPLETIONS = 0x01
INHIBIT_EXPLICIT_COMPLETIONS = 0x02


# Global {{{1
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

# Plugin interface {{{1
# plugin_path = []

def add_path(package_path):
    pass
    # global plugin_path
    # plugin_path +=  package_path
    # plugin_path = [x for i,x in enumerate(plugin_path) if plugin_path.index(x) == i]
    # sys.path += package_path
    # sys.path = [x for i,x in enumerate(sys.path) if sys.path.index(x) == i]

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
    modulename, ext = os.path.splitext(os.path.basename(fname))
    if sys.modules.has_key(modulename):
        return
    imp.load_source(modulename, fname)

def run_window_command(command_name, args = []):
    _window.run_command(command_name, args)

def run_text_command(command_name, args = []):
    _window.active_view().run_command(command_name, args)

def run_command(command_name, args = []):
    """
    Runs the named ApplicationCommand.
    """
    try:
        plugin = _find_command(command_name, sublime_plugin.ApplicationCommand.__subclasses__())
        command = plugin()
        command.run() # TODO args
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
def on_new(view = None): _call_event_listeners(view, 'on_new')
def on_clone(view = None): _call_event_listeners(view, 'on_clone')
def on_load(view = None): _call_event_listeners(view, 'on_load')
def on_close(view = None): _call_event_listeners(view, 'on_close')
def on_pre_save(view = None): _call_event_listeners(view, 'on_pre_save')
def on_post_save(view = None): _call_event_listeners(view, 'on_post_save')
def on_modified(view = None): _call_event_listeners(view, 'on_modified')
def on_selection_modified(view = None): _call_event_listeners(view, 'on_selection_modified')
def on_activated(view = None): _call_event_listeners(view, 'on_activated')
def on_deactivated(view = None): _call_event_listeners(view, 'on_deactivated')
# def on_query_context(view = None): pass

def on_query_completions(line = -1, col = -1, prefix = '', view = None):
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
    def __init__(self, setting_filename):
        self.settings = Settings._load(setting_filename)

    def __getitem__(self, key):
      return self.settings[key]

    def __setitem__(self, key, value):
      self.settings[key] = value

    def get(self, name, default = None):
        if self.settings.has_key(name):
            return self.settings[name]
        else:
            # TODO raise if default = None
            return default

    def set(self, name, value):
        self.settings[name] = value

    def erase(self, name):
        del self.settings[name]

    def has(self, name):
        return self.settings.has_key(name)

    def add_on_change(self, key, on_change):
        pass # TODO

    def clear_on_change(self, key):
        pass # TODO

    @staticmethod
    def _load(setting_filename):
        """ required path relative to package's root directory.
        >>> s = Settings._load('SublimeClang.sublime-settings')
        >>> s['enabled']
        True
        >>> s['error_marks_on_panel_only']
        False
        """
        files = compat.globpath(setting_filename)
        if not files:
            return {}

        with open(files[0], 'r') as f:
            text = f.read()

        # TODO remove block comments?
        text = re.sub(r'//.*', '', text) # remove line comments.
        return json.loads(text)

# Edit {{{1
class Edit(object):
    pass


# Window {{{1
class Window(object):
    def __init__(self):
        pass

    def run_command(self, command_name, args = []):
        """
        Runs the named WindowCommand.
        """
        try:
            plugin = _find_command(command_name, sublime_plugin.WindowCommand.__subclasses__())
            command = plugin(self)
            command.run() # TODO args
        finally:
            pass

    def active_view(self):
        return View()

    def open_file(self, target, flags = None):
        compat.message('Window.open_file: ' + target)
        m = re.match(r'^(.*):(\d+):(\d+)$', target)
        if m:
            path, line, col = m.groups()
            compat.open_file(path, int(line), int(col))
        else:
            # TODO ignore line, col
            compat.open_file(target)

    def show_quick_panel(self, items, on_done, flags = None):
        # TODO inputlist() or unite.vim
        compat.trace('Window.show_quick_panel: ' + repr(items))
        on_done(0)

    def folders(self):
        if not vimcompat.enable_vim:
            # FIXME it will crash
            return [os.getcwd()]
        else:
            return []


# View {{{1
class View(object):
    def __init__(self):
        self.vimwin = compat.getvimwindow()

    def run_command(self, command_name, args = []):
        """
        Runs the named TextCommand.
        """
        edit = self.begin_edit(command_name, args[:])
        try:
            plugin = _find_command(command_name, sublime_plugin.TextCommand.__subclasses__())
            command = plugin(self)
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
        return compat.getbufvar(self.vimwin.buffer.name, '&modified') != '0'

    def is_scratch(self):
        return compat.getbufvar(self.vimwin.buffer.name, '&buftype') != ''

    def sel(self):
        """
        Returns current cursor point or selection. (Zero based)
        """
        # vimwin.cursor[0]: line is 1 based.
        # vimwin.cursor[1]: col is zero based.
        cursor = self.vimwin.cursor
        return RegionSet(Region(self.text_point(cursor[0] - 1, cursor[1])), self)

    def insert(self, edit, point, string):
        # TODO what's edit?
        compat.message('View.insert: ' + str(point) + ' ' + string)
        # raise Exception('halt')

    def begin_edit(self, command, args):
        # Returns edit object.
        return {}

    def end_edit(self, edit):
        pass

    def rowcol(self, point):
        return point.get(self)

    def text_point(self, row, col):
        return Point(row, col, self)

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
        lines = self.vimwin.buffer[: line]
        last = self.vimwin.buffer[line][: col]
        return '\n'.join(lines) + '\n' + last

    def _get_rowcol(self, point):
        text = '\n'.join(self.vimwin.buffer[:])
        lines = text[: point].split('\n')
        line = len(lines)
        col = len(lines[-1])
        return (line, col)

    # def _range(self, begin_point, last_point):
    #     lines = self.vimwin.buffer[: line]
    #     last = self.vimwin.buffer[line][: col]

    def substr(self, point):
        """
        >>> v = View()
        >>> v.substr(v.text_point(0, 0))
        u'#'
        >>> v.substr(Region(0, 1))
        u'#'
        >>> v.substr(Region(0, 19))
        u'#include "stdio.h"\\n'
        >>> v.substr(Region(v.text_point(0, 0), v.text_point(0, 5)))
        u'#incl'
        >>> v.substr(Region(v.text_point(11, 1), v.text_point(11, 6)))
        u'type1'
        >>> v._get_match_pos(r'\w+', '\\tt.member1 = 1;', 4)
        (3, 10)
        >>> v.word(v.text_point(12, 4)).get(v)
        ((12, 3), (12, 10))
        >>> v.substr(v.word(v.text_point(12, 4)))
        u'member1'
        """
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
        """
        >>> v = View()
        >>> v.substr(v.line(v.text_point(0, 0)))
        u'#include "stdio.h"\\n'
        """
        # args is point or region
        if isinstance(point, Point):
            line, _ = self.rowcol(point)
            end = len(self.vimwin.buffer[line])
            return Region(self.text_point(line, 0), self.text_point(line, end))
        elif isinstance(point, Region):
            region = point
            # TODO
            # raise NotImplementedError
            return self.line(region.a)

    def word(self, point):
        """
        >>> v = View()
        >>> v.substr(v.word(v.text_point(11, 5)))
        u'type1'
        """
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
        >>> v = View()
        >>> v._get_match_pos(r'\w+', 'def aaa(arg):', 0)
        (0, 3)
        >>> v._get_match_pos(r'\w+', '\\tdef aaa(arg):', 6)
        (5, 8)
        """
        for m in re.finditer(pattern, text):
            if m.start() <= current_col <= m.end():
                return (m.start(), m.end())
        return None


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
        >>> v = View()
        >>> r = Region(v.text_point(0, 0), v.text_point(0, 1))
        >>> [i for i in RegionSet(r, v)][0].begin().get(v)
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
    def __init__(self, a, b = None):
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
        >>> v = View()
        >>> r = Region(v.text_point(0, 0), v.text_point(0, 1))
        >>> r.begin().get(v)
        (0, 0)
        """
        return min(self.a, self.b)

    def end(self):
        """
        >>> v = View()
        >>> r = Region(v.text_point(0, 0), v.text_point(0, 1))
        >>> r.end().get(v)
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
    NOTE line and column are zero based.
    """
    def __init__(self, line, col, view = None):
        if view is None:
            self._line = line
            self._col = col
            self._offset = None
        else:
            self._line = line
            self._col = col
            self._offset = len(view._substr_pos(line, col))

    def __str__(self):
        return 'Point(%d, %d)' % (self._line, self._col)

    def __cmp__(self, other):
        """
        TODO add test
        """
        if isinstance(other, Point):
            if self._line != other._line:
                return self._line - other._line
            else:
                return self._col - other._col
            # return self._offset - other._offset
        elif isinstance(other, int):
            return self._offset - other
        else:
            raise NotImplementedError

    def __sub__(self, other):
        if isinstance(other, int):
            if (self._col - other) >= 0:
                return Point(self._line, self._col - other)
            else:
                raise NotImplementedError
            # offset = self.offset - other
            # return Point.fromint(offset)
        else:
            raise NotImplementedError

    def get(self, view):
        if self._offset is None or self._line >= 0:
            return (self._line, self._col)
        else:
            return view._get_rowcol(self._offset)

    @staticmethod
    def fromint(offset):
        # compat.trace('fromint: ' + str(type(offset)))
        if offset == 1:
            return Point(0, 0)
        else:
            point = Point(-1, -1)
            point._offset = offset
            return point


# Instances {{{1
compat = vimcompat.create_compat()
deferred = Deferred()
_window = Window()


# doctest
def _test():
    vimcompat.test = True
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
