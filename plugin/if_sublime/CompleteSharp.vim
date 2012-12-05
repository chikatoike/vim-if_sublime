if exists('g:loaded_if_sublime_completesharp')
  finish
endif
let g:loaded_if_sublime_completesharp = 1

let s:save_cpo = &cpo
set cpo&vim

if !exists('g:sublimeclang_package_path')
  let g:sublimeclang_package_path = if_sublime#default_package_path('CompleteSharp')
endif

call if_sublime#register_plugin(g:sublimeclang_package_path)

let &cpo = s:save_cpo
unlet s:save_cpo

" vim:sts=2 sw=2
