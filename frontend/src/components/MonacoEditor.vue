<template>
  <div ref="editorContainer" class="monaco-editor-container"></div>
</template>

<script setup>
import {onMounted, onUnmounted, ref, watch} from 'vue'

const props = defineProps({
  modelValue: {type: String, default: ''},
  language: {type: String, default: 'shell'},
  readOnly: {type: Boolean, default: false},
  height: {type: [String, Number], default: '300px'}
})

const emit = defineEmits(['update:modelValue'])
const editorContainer = ref(null)
let editor = null

// 👇 换行符标准化函数
const normalizeLineEndings = (text) => {
  if (!text) return text
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

const initEditor = async () => {
  const monico = await import('monaco-editor')

  if (props.language === 'shell') {
    monico.languages.registerCompletionItemProvider('shell', {
      provideCompletionItems: () => {
        const commands = [
          'ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'echo', 'cat', 'grep',
          'find', 'ps', 'kill', 'top', 'df', 'du', 'chmod', 'chown', 'tar',
          'wget', 'curl', 'ssh', 'scp', 'rsync', 'systemctl', 'journalctl',
          'docker', 'docker ps', 'docker-compose', 'git', 'python3', 'bash', 'sh'
        ]

        const suggestions = commands.map(cmd => ({
          label: cmd,
          kind: monico.languages.CompletionItemKind.Function,
          insertText: cmd,
          detail: 'Shell Command'
        }))

        return {suggestions}
      }
    })
  }

  if (editor) {
    editor.dispose()
  }

  editor = monico.editor.create(editorContainer.value, {
    value: normalizeLineEndings(props.modelValue), // 初始化时也标准化
    language: props.language,
    theme: window.$themeStore.isDark?'vs-dark':'vs-light',
    automaticLayout: true,
    minimap: {enabled: false},
    fontSize: 14,
    scrollBeyondLastLine: false,
    tabSize: 2,
    wordWrap: 'on',
    readOnly: props.readOnly,
    renderLineHighlight: 'none',
    overviewRulerLanes: 0,
    hideCursorInOverviewRuler: true,
    scrollbar: {
      vertical: 'visible',
      horizontal: 'visible',
      verticalScrollbarSize: 8,
      horizontalScrollbarSize: 8
    },
    suggest: {
      showWords: true,
      showSnippets: false
    },
    quickSuggestions: {
      other: true,
      comments: false,
      strings: true
    }
  })

  editor.onDidChangeModelContent(() => {
    let value = editor.getValue()
    value = normalizeLineEndings(value)
    emit('update:modelValue', value)
  })
}

// 监听 prop 变化
watch(() => props.modelValue, (newVal) => {
  if (editor) {
    const normalizedValue = normalizeLineEndings(newVal)
    if (editor.getValue() !== normalizedValue) {
      editor.setValue(normalizedValue)
    }
  }
})

watch(() => props.language, () => {
  initEditor()
})

onMounted(() => {
  initEditor()
})

onUnmounted(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<style scoped>
.monaco-editor-container {
  width: 100%;
  height: v-bind(height);
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}
</style>
