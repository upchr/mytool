// src/plugins/hljs.js
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import shell from 'highlight.js/lib/languages/shell'
// 按需添加你需要的语言

hljs.registerLanguage('python', python)
hljs.registerLanguage('shell', shell)

export default hljs
