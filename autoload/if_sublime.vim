let s:save_cpo = &cpo
set cpo&vim

let g:vimsublime_filetype = {
      \ 'c': "c",
      \ 'cpp': "c++",
      \ }

let s:package_path = get(s:, 'package_path', {})

let s:is_windows = has('win16') || has('win32') || has('win64')
let s:is_cygwin = has('win32unix')
let s:is_mac = !s:is_windows && !s:is_cygwin
      \ && (has('mac') || has('macunix') || has('gui_macvim') ||
      \   (!executable('xdg-open') && system('uname') =~? '^darwin'))

function! if_sublime#default_package_path(package)
  if s:is_windows || s:is_cygwin
    return expand('$APPDATA/Sublime Text 2/Packages/') . a:package
  elseif s:is_mac
    return expand('~/Library/Application Support/Sublime Text 2/Packages/') . a:package
  else " linux
    return expand('~/.config/sublime-text-2/Packages/') . a:package
  endif
endfunction

function! if_sublime#is_windows()
  return s:is_windows
endfunction

function! s:add_path(python_path)
  python <<EOM
# coding=utf-8
import sys, vim
# sys.path = list(set(sys.path + list(vim.eval('a:python_path'))))
sys.path += list(vim.eval('a:python_path'))
sys.path = [x for i,x in enumerate(sys.path) if sys.path.index(x) == i]
EOM
endfunction

function! if_sublime#loaded_files()
  python import sys, os
  return pyeval('{ os.path.abspath(module.__file__): key for key, module in sys.modules.items() if hasattr(module, "__file__") }')
endfunction

function! if_sublime#register_plugin(path)
  let list = type(a:path) == type([]) ? a:path : [a:path]

  for path in list
    let s:package_path[path] = 0
  endfor
endfunction

function! if_sublime#load_plugin(path)
  let list = type(a:path) == type([]) ? a:path : [a:path]
  call if_sublime#register_plugin(list)

  python import vim, sublime
  python sublime.load_plugin(vim.eval('list'))
endfunction

function! s:load_all()
  python import vim, sublime
  for path in keys(s:package_path)
    python sublime.load_plugin([vim.eval('path')])
  endfor
endfunction

function! if_sublime#run_text_command(command_name, ...)
  call s:load_all()
  python import vim, sublime
  python sublime.run_text_command(vim.eval('a:command_name'))
endfunction

function! if_sublime#test_completion()
  let cur_text = strpart(getline('.'), 0, col('.') - 1)
  let prefix = matchstr(cur_text, '\w\+$')
  let prefix .= '' " work around.
  return s:on_query_completions(line('.'), col('.') - 2, prefix, 1)
endfunction

function! if_sublime#get_complete_words(cur_keyword_pos, cur_keyword_str)
  let col = a:cur_keyword_pos + strlen(a:cur_keyword_str)
  return s:on_query_completions(line('.'), col, a:cur_keyword_str, 0)[0]
endfunction

function! s:on_query_completions(line, col, prefix, interactive)
  call s:load_all()

  python import vim, vimcompat
  python vimcompat.debug = False if vim.eval('a:interactive') == '0' else True

  " TODO use vim.bindeval
  python import vim, sublime
  " return pyeval('sublime.on_query_completions(int(vim.eval("a:line")), int(vim.eval("a:col")), vim.eval("a:prefix"))')
  python sublime.temp = sublime.on_query_completions(int(vim.eval("a:line")), int(vim.eval("a:col")), vim.eval("a:prefix"))
  return pyeval('sublime.temp')
endfunction

function! if_sublime#complete(findstart, base)
  if a:findstart
    let cur_text = strpart(getline('.'), 0, col('.') - 1)
    " TODO keyword pattern
    return match(cur_text, '\w\+$')
  endif

  " TODO snippet
  let completions = if_sublime#get_complete_words(col('.') - 1, a:base)
  let list = []
  for [snippet, word] in completions
    call add(list, { 'word' : word, 'menu' : '[sublime] ' . snippet })
    " call add(list, { 'word' : word, 'abbr' : snippet, 'menu' : '[sublime]' })
  endfor

  return list
endfunction

function! if_sublime#scope()
  return s:
endfunction

call s:add_path([expand('<sfile>:p:h:h') . '/if_sublime'])

function! if_sublime#debug_reload()
  python <<EOM
# coding=utf-8
# NOTE: take care of module dependencies
try:
  import vimcompat; reload(vimcompat)
  import sublime; reload(sublime)
  vimcompat.debug = True
except ImportError:
  pass
EOM
endfunction

" call if_sublime#debug_reload()

let &cpo = s:save_cpo
unlet s:save_cpo

" vim:sts=2 sw=2
