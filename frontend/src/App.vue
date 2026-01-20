<template>
  <n-message-provider>
    <n-space vertical>

      <!-- 固定顶部header -->
      <n-page-header subtitle="让你的灵感有迹可循，让你的设备如臂使指。"  class="myheader">
        <template #title>
          <a href="https://github.com/upchr/mytool/" style="text-decoration: none; color: inherit">ToolsPlus</a>
        </template>
        <template #avatar>
          <n-avatar src="/ICON_256.PNG"/>
        </template>
        <template #extra>
          <n-button
              text
              tag="a"
              href="https://github.com/upchr/mytool/"
              target="_blank"
              style="font-size: 24px; margin-right: 10px"
          >
            <n-icon>
              <LogoGithub />
            </n-icon>
          </n-button>
          <n-button text style="font-size: 24px" @click="toggleMenu">
              <n-icon>
                <MenuIcon />
              </n-icon>
            </n-button>
        </template>
      </n-page-header>

      <n-layout has-sider class="mycontent">
        <!-- 固定左侧菜单 -->
        <n-layout-sider ref="siderRef"
            bordered
            collapse-mode="width"
            :collapsed-width="64"
            :width="240"
            :collapsed="collapsed"
            show-trigger
            @collapse="collapsed = true"
            @expand="collapsed = false"
            class="fixed-sider"
        >
          <n-menu
              v-model:value="activeKey"
              :collapsed="collapsed"
              :collapsed-width="64"
              :collapsed-icon-size="22"
              :options="menuOptions"
          />
        </n-layout-sider>

        <!-- 右侧内容区域 -->
        <n-layout class="content-layout" :style="collapsed?'margin-left: 60px;':'margin-left: 240px;'">
          <router-view />
        </n-layout>
      </n-layout>

      <!-- 固定底部footer -->
      <n-layout-footer bordered class="myfooter">
        ToolsPlus.ChrPlus
      </n-layout-footer>

    </n-space>
  </n-message-provider>
</template>

<script setup>
import {
  ReaderOutline as NoteIcon,
  TvOutline as PCIcon,
  AlarmOutline as ClockIcon,
  MenuOutline as MenuIcon,
  LogoGithub
} from "@vicons/ionicons5";
import { NIcon } from "naive-ui";
import { h, ref} from "vue";
import { RouterLink, RouterView } from "vue-router";
import { onClickOutside } from "@vueuse/core";
// 图标渲染函数
function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

// 路由配置（与 router.js 保持一致）
const routes = [
  { path: '/', label: '📝 便签管理', icon: NoteIcon, key: 'notes' },
  { path: '/nodes', label: '🖥️ 节点管理', icon: PCIcon, key: 'nodes' },
  { path: '/jobs', label: '⏰ 任务管理', icon: ClockIcon, key: 'jobs' }
];

// 动态生成菜单项
const menuOptions = routes.map(route => ({
  label: () => h(
      RouterLink,
      { to: route.path },
      { default: () => route.label }
  ),
  key: route.key,
  icon: renderIcon(route.icon)
}));

const activeKey = ref(null);
const collapsed = ref(true);
const siderRef = ref(null)

onClickOutside(
    siderRef,
    () => {
      collapsed.value = true
    },
    {
      ignore: ['.n-button', '.menu-trigger'],
      detectIframe: false,
      event: 'click',
      capture: true
    }
)
/*onClickOutside(
    siderRef,
    () => {
      collapsed.value = true
    },
    {
      ignore: ['.n-button', '.menu-trigger']
    }
)*/
const toggleMenu = () => {
  collapsed.value = !collapsed.value;
};
</script>

<style scoped>
/* 保证页面占满全屏 */
.myheader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: white;
  padding: 10px 20px;
  height: 5vh;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* 添加阴影效果 */
}

@media (max-width: 2000px) {
  .myheader {
    height: 9vh;
  }
}
/* 固定footer，底部 */
.myfooter {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: #f0f0f0;
  text-align: center;
  padding: 10px 0;
}

/* 固定左侧菜单 */
.mycontent .fixed-sider {
  position: fixed;
  top: 5vh; /* header下方 */
  left: 0;
  bottom: 60px; /* 留出footer的空间 */
  height: calc(100vh - 5vh); /* 满屏高度，减去header和footer */
  z-index: 1000;
}

@media (max-width: 2000px) {
  .mycontent .fixed-sider{
    top: 9vh; /* header下方 */
    height: calc(100vh - 9vh); /* 满屏高度，减去header和footer */
  }
}
/* 中间内容区域 */
.mycontent .content-layout {
  margin-top: 5vh; /* 给content留出header的空间 */
  margin-bottom: 60px; /* 给content留出footer的空间 */
  padding: 20px; /* 给content添加内边距 */
}


@media (max-width: 2000px) {
  .mycontent .content-layout {
    margin-left: 5vw !important; /* 小屏幕时 margin-left 为 0px */
    margin-top: 4vw !important; /* 小屏幕时 margin-left 为 0px */
  }
}
</style>
