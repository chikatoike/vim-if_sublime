if exists('g:loaded_if_sublime_sublimelang')
  finish
endif
let g:loaded_if_sublime_sublimelang = 1

let s:save_cpo = &cpo
set cpo&vim

if !exists('g:sublimeclang_package_path')
  let g:sublimeclang_package_path = if_sublime#default_package_path('SublimeClang')
endif

call if_sublime#register_plugin(g:sublimeclang_package_path)

let $PATH .= (if_sublime#is_windows() ? ';' : ':') . g:sublimeclang_package_path

command! SublimeTextCommandClangGotoDef call if_sublime#run_text_command('clang_goto_def')

let &cpo = s:save_cpo
unlet s:save_cpo

" vim:sts=2 sw=2
