<!-- src/App.vue -->
<template>
  <n-message-provider>
    <div class="min-h-screen bg-gray-50 mx-5 pb-20">
      <!-- 导航栏 -->
      <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" style="text-align: center; font-size: 20px">
          <div class="flex justify-between h-16">
            <div class="flex">
              <router-link to="/" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md">
                <span class="font-bold text-lg">📝 便签管理</span>
              </router-link>
              <router-link to="/nodes" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md ml-4">
                <span class="font-bold text-lg">🖥️ 节点管理</span>
              </router-link>
              <router-link to="/jobs" class="flex items-center px-2 text-gray-900 hover:bg-gray-100 rounded-md ml-4">
                <span class="font-bold text-lg">⏰ 任务管理</span>
              </router-link>
            </div>
          </div>
        </div>
      </nav>

      <!-- 主内容 -->
      <main class="py-6">
        <router-view />
      </main>

      <!-- 固定 Footer -->
      <footer class="bg-white shadow-inner fixed bottom-0 left-0 right-0 z-10" style="text-align: center">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
          © 2026 定时任务管理系统
        </div>
      </footer>
    </div>
  </n-message-provider>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>
