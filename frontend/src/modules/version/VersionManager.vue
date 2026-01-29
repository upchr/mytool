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
        <n-space v-if="!goUpdateIng && !versionInfo.updatable">已是最新版本！</n-space>

      </n-card>

      <n-card title="升级脚本" style="margin-bottom: 16px">
        <n-tabs type="line" animated>
          <n-tab-pane name="飞牛" tab="飞牛">
            <n-card title="飞牛升级脚本" hoverable style="height:60vh;overflow-y: auto;overflow-x: auto">
              <template #header-extra>
                <n-button type="info" size="small" @click="copy(fpk_code)">
                  复制
                </n-button>
              </template>
              <n-code :code="fpk_code" language="shell" show-line-numbers/>
            </n-card>
            <!-- 操作提示 -->
            <n-alert type="warning" class="mt-4">
              <template #icon>
                <n-icon><WarningOutline /></n-icon>
              </template>
              飞牛应用更新，可直接复制上面脚本到当前节点的任务管理中，执行。
            </n-alert>
          </n-tab-pane>
          <n-tab-pane name="Docker" tab="Docker">
            <n-card title="Docker脚本" hoverable style="height:60vh;overflow-y: auto;overflow-x: auto">
              <template #header-extra>
                <n-button type="info" size="small" @click="copy(docker_code)">
                  复制
                </n-button>
              </template>
              <n-code :code="docker_code" language="shell" show-line-numbers/>
            </n-card>
            <!-- 操作提示 -->
            <n-alert type="warning" class="mt-4">
              <template #icon>
                <n-icon><WarningOutline /></n-icon>
              </template>
              docker、docker compose启动时：<br>
              直接更新最新latest镜像，再重新创建即可。<br>
              或者复制上述脚本执行。
            </n-alert>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-space>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref} from 'vue'
import { NIcon, NButton} from 'naive-ui'
import {CloudDownloadOutline as UpdateIcon, WarningOutline} from '@vicons/ionicons5'
import axios from 'axios'

const goUpdateIng = ref(false)
const fpk_code = ref(`#!/bin/bash
BASE_DIR="/mydata/fpk"
mkdir -p $BASE_DIR

LOG_FILE="$BASE_DIR/update.log"
SH_FILE="$BASE_DIR/update_toolsplus.sh"
FPK_DIR="$BASE_DIR/FnDepot"
COMPOSE_FILE="/var/apps/toolsplus/target/docker/docker-compose.yaml"
REPO_URL="https://gitee.com/upchr/FnDepot.git"

#tee $SH_FILE <<EOF
cat > $SH_FILE <<EOF
#!/bin/bash
set -e  # 遇错即停

FPK_DIR="$FPK_DIR"
REPO_URL="$REPO_URL"
COMPOSE_FILE="$COMPOSE_FILE"

echo "-----------------------"
START_TIME=\\$(date +%s)
echo "[\\$(date +'%Y-%m-%d %H:%M:%S')] 开始更新 ..."

# === 1. 更新或克隆仓库 ===
if [ -d "$FPK_DIR" ]; then
  echo "开始更新 FnDepot 仓库..."
  cd "$FPK_DIR"
  git pull
  echo "更新完成！"
else
  echo "拉取 FnDepot 仓库中..."
  git clone "$REPO_URL" "$FPK_DIR"
  echo "拉取完成！"
fi

# === 2. 读取最新版本（来自 fnpack.json）===
LATEST_VERSION=\\$(jq -r '.toolsplus.version' "$FPK_DIR/fnpack.json")
if [ -z "\\$LATEST_VERSION" ] || [ "\\$LATEST_VERSION" = "null" ]; then
  echo "❌ 无法从 fnpack.json 读取 version 字段"
  exit 1
fi
echo "最新版本: v\\$LATEST_VERSION"

# === 3. 读取当前部署的镜像版本（来自 docker-compose.yaml）===
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "⚠️ docker-compose.yaml 不存在，重新安装"
  CURRENT_IMAGE_VERSION=""
else
  # 提取 image
  CURRENT_IMAGE=\\$(grep -E '^\\s*image:\\s*chrplus/toolsplus:' "$COMPOSE_FILE" | head -n1)
  if [ -z "\\$CURRENT_IMAGE" ]; then
    echo "⚠️ 未在 docker-compose.yaml 中找到 chrplus/toolsplus 镜像行"
    CURRENT_IMAGE_VERSION=""
  else
    # 提取标签部分（冒号后）
    CURRENT_IMAGE_VERSION=\\$(echo "\\$CURRENT_IMAGE" | sed -E 's/.*chrplus\\/toolsplus:(.*)/\\1/')
  fi
fi
echo "当前部署版本: \\$CURRENT_IMAGE_VERSION"

# === 4. 比较版本 ===
if [ "\\$LATEST_VERSION" = "\\\${CURRENT_IMAGE_VERSION#v}" ] || [ "v\\$LATEST_VERSION" = "\\$CURRENT_IMAGE_VERSION" ]; then
  echo "✅ 版本一致，无需更新"
  exit 0
else
  echo "🔁 版本不一致，准备更新应用..."
fi

# === 5. 执行更新流程 ===
cd "$FPK_DIR/toolsplus"

echo "正在卸载 toolsplus..."
appcenter-cli uninstall toolsplus
if [ \\$? -ne 0 ]; then
  echo "❌ 卸载失败"
  exit 1
fi

echo "正在安装新版本 FPK..."
appcenter-cli install-fpk toolsplus.fpk

echo "正在启动 toolsplus..."
appcenter-cli start toolsplus

END_TIME=\\$(date +%s)
DURATION=\\$((END_TIME - START_TIME))
echo "[\\$(date +'%Y-%m-%d %H:%M:%S')] ✅ toolsplus 已更新至 v\\$LATEST_VERSION！（耗时: \\\${DURATION}秒）"
echo "脚本执行完成！"
echo "-----------------------"
EOF

main() {
  echo "开始执行检测更新任务~"
  if [ -f "$LOG_FILE" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="\${LOG_FILE}.\${TIMESTAMP}.bak"
    echo "检测到已有日志，备份为 $BACKUP_FILE"
    mv "$LOG_FILE" "$BACKUP_FILE"
  fi

  chmod +x "$SH_FILE"
  "$SH_FILE" >> "$LOG_FILE" 2>&1 &

  tail -f "$LOG_FILE" &
  TAIL_PID=$!

  if timeout 120 sh -c 'while ! grep -q "✅.*\\(版本一致\\|已更新至\\)" '"$LOG_FILE"' 2>/dev/null; do sleep 0.5; done'; then
      echo ""
      echo "✅ 执行成功！"
      kill $TAIL_PID 2>/dev/null
      wait $TAIL_PID 2>/dev/null
      exit 0
  else
      echo ""
      echo "❌ 超时或失败"
      kill $TAIL_PID 2>/dev/null
      exit 1
  fi
}
main`)
const docker_code = ref(`#!/bin/bash
CONTAINER_NAME="toolsplus"
IMAGE_NAME="chrplus/toolsplus:latest"

BASE_DIR="/mydata/$CONTAINER_NAME"
mkdir -p "$BASE_DIR"

LOG_FILE="$BASE_DIR/update.log"
SH_FILE="$BASE_DIR/update_toolsplus.sh"
BACKUP_DIR="$BASE_DIR/data-backup"
DATA_DIR="$BASE_DIR/data"


cat > "$SH_FILE" <<EOF
#!/bin/bash
set -e

CONTAINER_NAME="$CONTAINER_NAME"
IMAGE_NAME="$IMAGE_NAME"
BACKUP_DIR="$BACKUP_DIR"
DATA_DIR="$DATA_DIR"

echo "-----------------------"
START_TIME=\\$(date +%s)
echo "[\\$(date +'%Y-%m-%d %H:%M:%S')] 开始更新 \\$CONTAINER_NAME..."

# 1. 创建备份目录
mkdir -p "\\$BACKUP_DIR"

# 2. 处理现有数据
if docker ps -a --format '{{.Names}}' | grep -q "^\\\${CONTAINER_NAME}\\$"; then
    echo "检测到现有容器，正在处理数据..."

    if docker exec "\\$CONTAINER_NAME" test -d /toolsplus/data 2>/dev/null; then
        if [ ! -d "\\$DATA_DIR" ] || [ -z "\\$(ls -A "\\$DATA_DIR" 2>/dev/null)" ]; then
            echo "从容器复制数据到持久化目录..."
            mkdir -p "\\$DATA_DIR"
            docker cp "\\\${CONTAINER_NAME}:/toolsplus/data/." "\\$DATA_DIR/"
        else
            echo "持久化目录已存在数据，跳过复制"
        fi

        echo "创建备份..."
        if [ -d "\\$BACKUP_DIR" ] && [ -n "\\$(ls -A "\\$BACKUP_DIR" 2>/dev/null)" ]; then
          TIMESTAMP=\\$(date +%Y%m%d_%H%M%S)
          mv "\\$BACKUP_DIR" "\\\${BACKUP_DIR}.\\$TIMESTAMP.bak"
        fi
        mkdir -p "\\$BACKUP_DIR"
        docker cp "\\\${CONTAINER_NAME}:/toolsplus/data/." "\\$BACKUP_DIR/"

        echo "停止并删除旧容器..."
        docker stop "\\$CONTAINER_NAME" 2>/dev/null || true
        docker rm "\\$CONTAINER_NAME" 2>/dev/null || true
    else
        echo "容器中没有 /toolsplus/data 目录，创建空数据目录..."
        mkdir -p "\\$DATA_DIR"
    fi
else
    if [ ! -d "\\$DATA_DIR" ]; then
        echo "首次安装，创建空数据目录..."
        mkdir -p "\\$DATA_DIR"
    else
        echo "使用现有数据目录"
    fi
fi

# 3. 拉取新镜像
echo "拉取新镜像..."
docker pull "\\$IMAGE_NAME"

# 4. 启动新容器
echo "启动新容器..."
docker run -d \\\\
  --name "\\$CONTAINER_NAME" \\\\
  -e TZ=Asia/Shanghai \\\\
  -v "\\$DATA_DIR":/toolsplus/data \\\\
  -p 16688:80 \\\\
  --restart unless-stopped \\\\
  "\\$IMAGE_NAME"

# 5. 清理旧的 toolsplus 镜像
echo "清理旧的 toolsplus 镜像..."
CURRENT_IMAGE_ID=\\$(docker inspect --format='{{.Image}}' "\\$CONTAINER_NAME" 2>/dev/null)

if [ -n "\\$CURRENT_IMAGE_ID" ]; then
    docker images 'chrplus/toolsplus' --format '{{.ID}}' | \\\\
      grep -v "^\\$CURRENT_IMAGE_ID\\$" | \\\\
      xargs -r docker rmi > /dev/null 2>&1 || true
fi

END_TIME=\\$(date +%s)
DURATION=\\$((END_TIME - START_TIME))
echo "[\\$(date +'%Y-%m-%d %H:%M:%S')] ✅ \\$CONTAINER_NAME 更新完成！（耗时: \\\${DURATION}秒）"
echo "脚本执行完成！"
echo "-----------------------"
EOF


main() {
  echo "开始执行检测更新任务~"
  if [ -f "$LOG_FILE" ]; then
      TIMESTAMP=$(date +%Y%m%d_%H%M%S)
      BACKUP_FILE="\${LOG_FILE}.\${TIMESTAMP}.bak"
      echo "检测到已有日志，备份为 $BACKUP_FILE"
      mv "$LOG_FILE" "$BACKUP_FILE"
  fi
  # 赋予执行权限
  chmod +x "$SH_FILE"

  # 启动后台任务
  "$SH_FILE" >> "$LOG_FILE" 2>&1 </dev/null &

  # 实时监控日志
  tail -f "$LOG_FILE" &
  TAIL_PID=$!

  # 等待成功标志（最多 120 秒）
  if timeout 120 sh -c 'while ! grep -q "✅.*更新完成" '"$LOG_FILE"' 2>/dev/null; do sleep 1; done'; then
      echo ""
      echo "✅ 成功检测到更新完成"
      kill $TAIL_PID 2>/dev/null
      wait $TAIL_PID 2>/dev/null
      exit 0
  else
      echo ""
      echo "❌ 超时或更新失败"
      kill $TAIL_PID 2>/dev/null
      exit 1
  fi
}
main
`)

const copy =  (text) => {
  window.$copyCode(text)
}


const versionInfo = ref({ current: '检查中~', latest: '', updatable: false,updated_at:'' })
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
                  window.$copyCode(`chrplus/toolsplus:${versionInfo.value.latest}`,e)
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
