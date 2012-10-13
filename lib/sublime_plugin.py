# Base classes of Sublime Text 2 Plugin.
# Reference: http://www.sublimetext.com/docs/2/api_reference.html

class EventListener(object):
    def on_new(self, view): pass
    def on_clone(self, view): pass
    def on_load(self, view): pass
    def on_close(self, view): pass
    def on_pre_save(self, view): pass
    def on_post_save(self, view): pass
    def on_modified(self, view): pass
    def on_selection_modified(self, view): pass
    def on_activated(self, view): pass
    def on_deactivated(self, view): pass
    def on_query_context(self, view, key, operator, operand, match_all): return None
    def on_query_completions(self, view, prefix, locations): return []

class ApplicationCommand(object):
    def run(self):
        pass

class WindowCommand(object):
    def __init__(self, window):
        self.window = window

    def run(self):
        pass

class TextCommand(object):
    def __init__(self, view):
        self.view = view

    def run(self, edit):
        pass
