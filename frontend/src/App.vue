<template>
  <n-config-provider :hljs="hljs" :theme="themeStore.theme">
    <n-message-provider>
    <n-notification-provider>
    <n-dialog-provider>
      <n-space vertical style="width: 100vw">
        <!-- 固定顶部header -->
        <n-page-header :subtitle="subtitle"  class="myheader"
                       :style="{
                        backgroundColor: themeStore.theme?.name === 'dark' ? 'rgb(24, 24, 28)' : 'white',
                        color: themeStore.theme?.name === 'dark' ? 'white' : 'black'
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
            <n-button text style="font-size: 24px;margin-right: 10px" @click="themeStore.toggleTheme">
              <n-icon>
                <SunIcon v-if="themeStore.theme?.name === 'dark'" />
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
          <div v-if="width<1000" class="menu-container" :class="{ 'menu-open': !collapsed }">
            <!-- 遮罩层 -->
            <div
                v-show="!collapsed"
                class="menu-overlay"
                @click="collapsed = true"
                @touchstart="collapsed = true"
            ></div>

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

          </div>
          <!-- 右侧内容区域 -->
          <n-layout class="content-layout" :style="collapsed?'margin-left: 60px;':'margin-left: 200px;'">
            <router-view />
          </n-layout>
        </n-layout>
        <!-- 固定底部footer -->
        <n-layout-footer bordered class="myfooter">
          <n-flex justify="space-between" size="large">
            <span></span>
            <span style="width:20%;">ToolsPlus.ChrPlus</span>
            <span  style="padding-right: 10px">

              <n-badge processing type="warning" style="position: fixed;right:30px;bottom: 5px">
                <n-avatar @click="goUpdate">{{versionInfo.current}}</n-avatar>
                <template #value >
                  <n-icon v-if="versionInfo.updatable" :component="UpdateIcon" />
                </template>
              </n-badge>
            </span>
          </n-flex>
        </n-layout-footer>
      </n-space>
    </n-dialog-provider>
    </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import {
  MenuOutline as MenuIcon,
  LogoGithub,
  SunnyOutline as SunIcon,
  MoonOutline as MoonIcon,
  CloudDownloadOutline as UpdateIcon,
} from "@vicons/ionicons5";
import {NIcon,NButton } from "naive-ui";
import {computed, h, onMounted, ref, watch} from "vue";
import {RouterLink, RouterView, useRouter} from "vue-router";
import {useWindowSize} from "@vueuse/core";
import hljs from './plugins/hljs' // 引入 hljs 配置

import axios from "axios";
/*import { darkTheme, useOsTheme } from "naive-ui";
const osTheme = useOsTheme();
const theme = ref(null);
const initTheme =()=>{
 theme.value = osTheme.value === "dark" ? darkTheme : null;
}
const toggleTheme = () => {
  theme.value = theme.value?.name === 'dark' ? null :darkTheme;
};*/
import { useThemeStore } from '@/stores/theme'
const themeStore = useThemeStore()

// 图标渲染函数
function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

// 路由配置（与 router.js 保持一致）
import {routeLabels} from "./router/index.js";
const routes = routeLabels;

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

// onClickOutside(
//     siderRef,
//     () => {
//       collapsed.value = true
//     },
//     {
//       ignore: ['.n-button', '.menu-trigger'],
//       detectIframe: false,
//       event: 'click',
//       capture: true
//     }
// )

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

const versionInfo = ref({ current: '', latest: '', updatable: false,updated_at:'' })
const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
const getVersion = async () => {
  try {
    const res = await axios.get(`/api/version/`)
    versionInfo.value = res.data
  } catch (error) {
    window.$message?.error('获取当前版本失败')
  }
}

const router = useRouter()  // 获取 router 实例
const goToAbout = () => {
  router.push('/versions')  // 跳转到 /versions 路由
}
const goUpdate = async () => {
  if(!versionInfo.value.updatable){
    return
  }

  function notice() {
    let markAsRead = false;
    const n = window.$notification.info({
      title: "升级提醒",
      content: () => {
        const links = [
          { url: 'https://github.com/upchr/FnDepot', text: 'GitHub - FnDepot' },
          { url: 'https://gitee.com/upchr/FnDepot', text: 'Gitee - FnDepot' },
          { url: 'https://github.com/upchr/mytool', text: 'GitHub - mytool' }
        ]

        return h('div', { class: 'upgrade-notification' }, [
          // 版本信息
          h('div', { class: 'version-section' }, [
            h('p', { class: 'section-title' }, '版本信息'),
            h('div', { class: 'version-info' }, [
              h('div', { class: 'version-row' }, [
                h('span', { class: 'label ' }, '最新版本：'),
                h('span', { class: 'value newVersion' }, versionInfo.value.latest)
              ]),
              h('div', { class: 'version-row' }, [
                h('span', { class: 'label' }, '当前版本：'),
                h('span', { class: 'value' }, versionInfo.value.current)
              ])
            ])
          ]),

          // Git 地址
          h('div', { class: 'links-section' }, [
            h('p', { class: 'section-title' }, '获取Git地址：'),
            ...links.map(link =>
                h('div', { class: 'link-item' }, [
                  h('a', {
                    href: link.url,
                    target: '_blank',
                    class: 'git-link',
                    onClick: (e) => {
                      e.stopPropagation()
                      window.open(link.url, '_blank')
                    }
                  }, link.text)
                ])
            )
          ]),

          // Docker 镜像
          h('div', { class: 'docker-section' }, [
            h('p', { class: 'section-title' }, '最新docker镜像：'),
            h('div', { class: 'docker-image' }, [
              h('code', { class: 'docker-tag' }, `chrplus/toolsplus:${versionInfo.value.latest}`),
              h('button', {
                class: 'copy-btn',
                onClick: (e) => {
                  window.$copyCode(`chrplus/toolsplus:${versionInfo.value.latest}`,e)
                  // handleCopy
                  /*e.stopPropagation()
                  navigator.clipboard.writeText(`chrplus/toolsplus:${versionInfo.value.latest}`)
                  window.$message.success('已复制到剪贴板')*/
                }
              }, '复制')
            ])
          ]),

          // 提示信息
          h('div', { class: 'hint-section' }, [
            h('p', { class: 'section-title' }, '应用升级'),
            h('div', { class: '' }, [
              h('div', { class: '' }, [
                h('span', { class: 'label' }, '可去"关于"菜单，查看详细说明。'),
                h('button', {
                  class: 'copy-btn',
                  onClick: (e) => {
                    e.stopPropagation()
                    goToAbout()  // 使用 goToAbout 函数
                  }
                }, '关于')
              ])
            ])
          ])
        ])
      },
      meta: formatDate(versionInfo.value.updated_at),
      action: () => h(
          NButton,
          {
            text: true,
            type: "primary",
            onClick: () => {
              markAsRead = true;
              n.destroy();
            }
          },
          {
            default: () => "已读"
          }
      ),
      onClose: () => {
        if (!markAsRead) {
          window.$message.warning("请设为已读");
          return false;
        }
      }
    });
  }
  const res = await axios.get(`/api/version/lastVersion`)
  versionInfo.value = res.data
  notice()
}
onMounted(async () => {

  // themeStore.initTheme()
  await getVersion()
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
  z-index: 1001;
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
  z-index: 1001;
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

.menu-container {
  position: relative;
}

.menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999; /* 确保在菜单下层 */
}

.n-layout-sider {
  z-index: 1000; /* 确保在遮罩层上层 */
  position: relative;
}

/* 移动端样式 */
@media (max-width: 1000px) {
  .menu-overlay {
    display: block;
  }

  .n-layout-sider {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1000;
    //box-shadow: 2px 0 6px rgba(0, 0, 0, 0.15);
  }
}
</style>
