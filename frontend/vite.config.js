const { defineConfig } = require('vite')
const vue = require('@vitejs/plugin-vue')

module.exports = defineConfig({
  plugins: [vue()],

  // 开发服务器配置（仅 npm run dev 时生效）
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // rewrite 不是必须的，因为 FastAPI 路径就是 /api/...
        rewrite: (path) => path.replace(/^\/api/, '/')
      }
    }
  },

  // 构建配置（npm run build 时生效）
  build: {
    outDir: 'dist',        // 👈 关键！指定输出目录
    emptyOutDir: true,     // 构建前清空 dist
    sourcemap: false       // 生产可关闭
  }
})
