// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import path from 'path' // 导入 path 模块

export default defineConfig({
  // GitHub Pages 部署需要设置 base（通过 VITE_GITHUB_PAGES=true 启用）
  // Docker/Railway 等其他部署不需要设置
  base: process.env.VITE_GITHUB_PAGES === 'true' ? '/mytool/' : '/',
  
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
  },
  // 定义环境变量
  define: {
    __API_BASE_URL__: JSON.stringify(
      process.env.VITE_API_BASE_URL || 
      (process.env.NODE_ENV === 'production' 
        ? '' // 生产环境使用相对路径，由 GitHub Actions 注入
        : 'http://localhost:8000')
    )
  }
})
