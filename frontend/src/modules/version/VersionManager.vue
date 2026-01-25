<template>
  <n-card title="👤 关于" class="mb-6">
    <n-space justify="end" style="margin-bottom: 10px">
      <n-badge processing type="warning">
        <n-button type="error"
                  :loading="goUpdateIng"
                  @click="goUpdate">
          检查更新
        </n-button>
        <template #value >
          <n-icon v-if="versionInfo.updatable" :component="UpdateIcon" />
        </template>
      </n-badge>

<!--      <n-button type="error"
          :loading="goUpdateIng"
          @click="goUpdate">
        检查更新
      </n-button>-->
    </n-space>
    <n-space vertical>
      <n-card title="版本" hoverable>
        <n-space>当前版本：<n-space >{{versionInfo.current}}</n-space></n-space>
        <n-space v-if="versionInfo.updatable">最新版本：<n-space wrap-item item-style="color: red;font-weight: bold">{{versionInfo.latest}}</n-space></n-space>
        <n-space v-if="versionInfo.updatable">更新日期：<n-space >{{formatDate(versionInfo.updated_at)}}</n-space></n-space>
        <n-space v-else>已是最新版本！</n-space>

      </n-card>
      <n-card title="飞牛升级脚本" hoverable style="overflow-y: auto;overflow-x: auto">
        <template #header-extra>
          <n-button @click="copyText">
            Copy
          </n-button>
        </template>
        <n-code :code="code" language="shell" show-line-numbers/>
      </n-card>


      <!-- 操作提示 -->
      <n-alert type="warning" class="mt-4">
        <template #icon>
          <n-icon><WarningOutline /></n-icon>
        </template>
        飞牛应用更新，可直接复制上面脚本到当前节点的任务管理中，执行。
      </n-alert>

    </n-space>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref} from 'vue'
import { NIcon, NButton} from 'naive-ui'
import {CloudDownloadOutline as UpdateIcon, WarningOutline} from '@vicons/ionicons5'
import axios from 'axios'

const goUpdateIng = ref(false)
const code = ref(`
tee /mydata/update_toolsplus.sh <<'EOF'
#!/bin/bash
DIR="/mydata/fpk/FnDepot"
REPO_URL="https://gitee.com/upchr/FnDepot.git"

if [ -d "$DIR" ]; then
  echo "开始更新~"
  cd "$DIR"
  git pull
  echo "更新完成！"
else
  echo "拉取仓库中~"
  git clone "$REPO_URL" "$DIR"
  echo "拉取仓库完成！"
fi

echo "$DIR/toolsplus"
cd "$DIR/toolsplus"
appcenter-cli uninstall toolsplus
if [ $? -ne 0 ]; then
  echo '卸载失败'
  exit 1
fi
appcenter-cli install-fpk toolsplus.fpk
appcenter-cli start toolsplus
EOF

chmod +x /mydata/update_toolsplus.sh
nohup /mydata/update_toolsplus.sh >> update.log 2>&1 &
`)

const copyText = (e) => {
  e.stopPropagation();  // 阻止事件冒泡
  navigator.clipboard.writeText(code.value)  // 将代码内容复制到剪贴板
      .then(() => {
        window.$message.success('已复制到剪贴板');  // 显示成功消息
      })
      .catch((err) => {
        window.$message.error('复制失败，请重试');  // 复制失败的错误处理
      });
}
const versionInfo = ref({ current: '', latest: '', updatable: false,updated_at:'' })
const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',  // 显示四位年份
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
const getVersion = async (flag = false) => {
  try {
    goUpdateIng.value = true
    const res = await axios.get(`/api/version/lastVersion`)
    versionInfo.value = res.data
    if(flag && versionInfo.value.updatable){
      window.$message?.warning(`有版本可更新！${versionInfo.value.latest}`)
    }
  } catch (error) {
    window.$message?.error('获取当前版本失败')
  }finally {
    goUpdateIng.value = false
  }
}
const goUpdate = async () => {
  await getVersion()
  if(!versionInfo.value.updatable){
    return
  }

  function notice() {
    let markAsRead = false;
    /*const n = window.$notification.info({
      title: "升级提醒",
      content: () => h('div', [
        h('p', '有版本可升级：'),
        h('p', [
          h('strong', '最新版本：'),
          h('span', versionInfo.value.latest)
        ]),
        h('p', [
          h('strong', '当前版本：'),
          h('span', versionInfo.value.current)
        ]),
        h('br'),
        h('p', '获取Git地址：'),
        h('p', [
          h('a', {
            href: 'https://github.com/upchr/FnDepot',
            target: '_blank',
            style: 'color: #1890ff; text-decoration: none;'
          }, 'https://github.com/upchr/FnDepot')
        ]),
        h('p', [
          h('a', {
            href: 'https://gitee.com/upchr/FnDepot',
            target: '_blank',
            style: 'color: #1890ff; text-decoration: none;'
          }, 'https://gitee.com/upchr/FnDepot')
        ]),
        h('br'),
        h('p', '最新docker镜像：'),
        h('p', [
          h('code', `chrplus/toolsplus:${versionInfo.value.latest}`)
        ]),
        h('br'),
        h('p', '飞牛应用升级：可去"关于"菜单，查看详细说明。')
      ]),
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
    });*/
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
                  e.stopPropagation()
                  navigator.clipboard.writeText(`chrplus/toolsplus:${versionInfo.value.latest}`)
                  window.$message.success('已复制到剪贴板')
                }
              }, '复制')
            ])
          ]),
/*
          // 提示信息
          h('div', { class: 'hint-section' }, [
            h('p', { class: 'section-title' }, '应用升级'),
            h('div', { class: '' }, [
              h('div', { class: '' }, [
                h('span', { class: 'label' }, '飞牛可去"关于"菜单，查看详细说明。'),
              ])
            ])
          ])*/
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
  notice()
}

onMounted(async () => {
  await getVersion(true)
})
</script>

<style>
</style>
