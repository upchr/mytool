<template>
  <n-message-provider>
    <n-space vertical>
<!--    <n-switch v-model:value="collapsed" />-->
    <n-layout has-sider>
      <n-layout-sider
          bordered
          collapse-mode="width"
          :collapsed-width="64"
          :width="240"
          :collapsed="collapsed"
          show-trigger
          @collapse="collapsed = true"
          @expand="collapsed = false"
      >
        <n-menu
            v-model:value="activeKey"
            :collapsed="collapsed"
            :collapsed-width="64"
            :collapsed-icon-size="22"
            :options="menuOptions"
        />
      </n-layout-sider>
      <n-layout>
        <router-view />
      </n-layout>
    </n-layout>
  </n-space>
  </n-message-provider>
</template>

<script setup>
import {
  ReaderOutline as NoteIcon,
  TvOutline as PCIcon,
  AlarmOutline as ClockIcon,

} from "@vicons/ionicons5";
import { NIcon } from "naive-ui";
import { h, ref } from "vue";
import {RouterLink,RouterView} from "vue-router";

// 图标渲染函数
function renderIcon(icon) {
  return () => h(NIcon, null, {default: () => h(icon)});
}

// 路由配置（与 router.js 保持一致）
const routes = [
  {path: '/', label: '📝 便签管理', icon: NoteIcon, key: 'notes'},
  {path: '/nodes', label: '🖥️ 节点管理', icon: PCIcon, key: 'nodes'},
  {path: '/jobs', label: '⏰ 任务管理', icon: ClockIcon, key: 'jobs'}
];

// 动态生成菜单项
const menuOptions = routes.map(route => ({
  label: () => h(
      RouterLink,
      {to: route.path},
      {default: () => route.label}
  ),
  key: route.key,
  icon: renderIcon(route.icon)
}));

const activeKey = ref(null);
const collapsed = ref(true);
</script>
