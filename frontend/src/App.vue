<template>
  <n-config-provider :hljs="hljs" :theme="theme">
    <n-notification-provider>
    <n-dialog-provider>
    <n-message-provider>
      <n-space vertical style="width: 100vw">
        <!-- 固定顶部header -->
        <n-page-header :subtitle="subtitle"  class="myheader"
                       :style="{
                        backgroundColor: theme?.name === 'dark' ? 'rgb(24, 24, 28)' : 'white',
                        color: theme?.name === 'dark' ? 'white' : 'black'
                      }"
        >
          <template #title>ToolsPlus
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
            <n-button text style="font-size: 24px;margin-right: 10px" @click="toggleTheme">
              <n-icon>
                <SunIcon v-if="theme?.name === 'dark'" />
                <MoonIcon v-else />
              </n-icon>
            </n-button>
            <n-button text style="font-size: 24px;" @click="toggleMenu">
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
              :collapsed-width="60"
              :width="190"
              :collapsed="collapsed"
              show-trigger
              @collapse="collapsed = true"
              @expand="collapsed = false"
              class="fixed-sider"
          >
            <n-menu
                v-model:value="activeKey"
                :collapsed="collapsed"
                :collapsed-width="60"
                :collapsed-icon-size="22"
                :options="menuOptions"
            />
          </n-layout-sider>

          <!-- 右侧内容区域 -->
          <n-layout class="content-layout" :style="collapsed?'margin-left: 60px;':'margin-left: 200px;'">
            <router-view />
          </n-layout>
        </n-layout>
        <!-- 固定底部footer -->
        <n-layout-footer bordered class="myfooter">
          ToolsPlus.ChrPlus
        </n-layout-footer>
      </n-space>
    </n-message-provider>
    </n-dialog-provider>
    </n-notification-provider>
  </n-config-provider>
</template>

<script setup>
import {
  ReaderOutline as NoteIcon,
  TvOutline as PCIcon,
  AlarmOutline as ClockIcon,
  MenuOutline as MenuIcon,
  LogoGithub,
  ServerOutline as DatabaseIcon,
  SunnyOutline as SunIcon,
  MoonOutline as MoonIcon,
} from "@vicons/ionicons5";
import { NIcon } from "naive-ui";
import {computed, h, onMounted, ref, watch} from "vue";
import { RouterLink, RouterView } from "vue-router";
import {onClickOutside, useWindowSize} from "@vueuse/core";
import hljs from './plugins/hljs' // 引入 hljs 配置

import { darkTheme, useOsTheme } from "naive-ui";
const osTheme = useOsTheme();
const theme = ref(null);
const initTheme =()=>{
 theme.value = osTheme.value === "dark" ? darkTheme : null;
}
const toggleTheme = () => {
  theme.value = theme.value?.name === 'dark' ? null :darkTheme;
};

// 图标渲染函数
function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

// 路由配置（与 router.js 保持一致）
const routes = [
  { path: '/', label: '📝 便签管理', icon: NoteIcon, key: 'notes' },
  { path: '/nodes', label: '🖥️ 节点管理', icon: PCIcon, key: 'nodes' },
  { path: '/jobs', label: '⏰ 任务管理', icon: ClockIcon, key: 'jobs' },
  { path: '/database', label: '💾 数据管理', icon: DatabaseIcon, key: 'database' }
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



const { width } = useWindowSize(); // 获取窗口宽度

// 计算 subtitle 根据窗口宽度的变化
const subtitle = computed(() => {
  if (width.value < 1100) {
    return '猜猜怎么用。'; // 如果宽度小于 1100px, subtitle 设置为空
  } else {
    return '让你的灵感有迹可循，让你的设备如臂使指。'; // 否则显示默认的 subtitle 文本
  }
});

onMounted(async () => {
  initTheme()
})
</script>

<style scoped>
.myheader,
.myfooter {
  transition: background-color 0.3s ease, color 0.3s ease;
}
/* 保证页面占满全屏 */
.myheader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  //background-color: white;
  padding: 10px 20px;
  height: 50px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* 添加阴影效果 */
}

@media (max-width: 1000px) {
  .myheader {
    height: 50px;
  }
}
/* 固定footer，底部 */
.myfooter {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  //background-color: #f0f0f0;
  text-align: center;
  padding: 10px 0;
}
.mycontent{

}
/* 固定左侧菜单 */
.mycontent .fixed-sider {
  position: fixed;
  top: 50px; /* header下方 */
  left: 0;
  bottom: 60px; /* 留出footer的空间 */
  height: calc(100vh - 50px); /* 满屏高度，减去header和footer */
  z-index: 1000;
}

@media (max-width: 1000px) {
  .mycontent .fixed-sider{
    top: 50px; /* header下方 */
    height: 100vh; /* 满屏高度，减去header和footer */
  }
}
/* 中间内容区域 */
.mycontent .content-layout {
  margin-top: 50px; /* 给content留出header的空间 */
  margin-bottom: 60px; /* 给content留出footer的空间 */
  padding: 20px; /* 给content添加内边距 */
  height: calc(100vh - 50px); /* 满屏高度，减去header和footer */
}

@media (max-width: 1000px) {
  .mycontent .content-layout {
    margin-top: 20px !important; /* 小屏幕时 margin-left 为 0px */
    margin-left: 5vw !important; /* 小屏幕时 margin-left 为 0px */
  }
}
</style>
