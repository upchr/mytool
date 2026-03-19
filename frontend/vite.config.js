// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import path from 'path' // 导入 path 模块

export default defineConfig({
  plugins: [
    vue(),
    // 👇 添加自动按需引入
    Components({
      resolvers: [NaiveUiResolver()]
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')  // 配置 @ 指向 src 目录
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['chrmjj.fun','fnos.chrmjj.fun','chrmjj.fnos.net'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/'),
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false
  }
})
