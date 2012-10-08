let s:save_cpo = &cpo
set cpo&vim

let s:source = {
      \ 'name' : 'sublime_complete',
      \ 'kind' : 'ftplugin',
      \ 'filetypes': { 'c': 1, 'cpp': 1 },
      \ }

function! s:source.initialize()
endfunction

function! s:source.finalize()
endfunction

function! s:source.get_keyword_pos(cur_text)
  let pattern = neocomplcache#get_keyword_pattern()
  return match(a:cur_text, pattern)
endfunction

function! s:source.get_complete_words(cur_keyword_pos, cur_keyword_str)
  return []
"   return if_sublime#get_complete_words(a:cur_keyword_pos, a:cur_keyword_str)
endfunction

function! neocomplcache#sources#sublime_complete#define()
  return s:source
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo

" vim:sts=2 sw=2
