<template>
  <div class="plugin-market">
    <div class="header">
      <h2>🔌 插件市场</h2>
      <p>扩展MyTool功能，支持通知渠道、执行器、存储等多种插件</p>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索插件名称或描述..."
        clearable
        style="width: 300px"
        @input="loadPlugins"
      />
      <el-select v-model="filters.plugin_type" placeholder="插件类型" clearable @change="loadPlugins">
        <el-option label="全部" value="" />
        <el-option label="通知渠道" value="notification" />
        <el-option label="任务执行器" value="executor" />
        <el-option label="数据源" value="datasource" />
        <el-option label="触发器" value="trigger" />
        <el-option label="存储" value="storage" />
        <el-option label="AI引擎" value="ai" />
      </el-select>
      <el-select v-model="filters.is_official" placeholder="官方插件" clearable @change="loadPlugins">
        <el-option label="全部" :value="undefined" />
        <el-option label="官方" :value="true" />
        <el-option label="第三方" :value="false" />
      </el-select>
      <el-select v-model="filters.is_installed" placeholder="安装状态" clearable @change="loadPlugins">
        <el-option label="全部" :value="undefined" />
        <el-option label="已安装" :value="true" />
        <el-option label="未安装" :value="false" />
      </el-select>
      <el-button type="primary" @click="loadPlugins">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载中...
    </div>

    <!-- 插件列表 -->
    <div v-else-if="plugins.length" class="plugin-grid">
      <div
        v-for="plugin in plugins"
        :key="plugin.id"
        class="plugin-card"
        @click="openDetail(plugin)"
      >
        <div class="card-header">
          <span class="icon">{{ plugin.icon || '🔌' }}</span>
          <span class="name">{{ plugin.name }}</span>
          <el-tag v-if="plugin.is_official" size="small" type="success" class="official-tag">官方</el-tag>
          <el-tag v-if="plugin.is_installed" size="small" type="info">已安装</el-tag>
        </div>
        <div class="card-body">
          <p class="description">{{ plugin.description || '暂无描述' }}</p>
          <div class="meta">
            <span class="plugin-type" :class="`type-${plugin.plugin_type}`">
              {{ getPluginTypeLabel(plugin.plugin_type) }}
            </span>
            <span class="version">v{{ plugin.version }}</span>
          </div>
        </div>
        <div class="card-footer">
          <span class="downloads">
            <el-icon><Download /></el-icon>
            {{ plugin.download_count }}
          </span>
          <span v-if="plugin.rating_avg" class="rating">
            <el-icon><Star /></el-icon>
            {{ plugin.rating_avg.toFixed(1) }}
          </span>
          <span class="author">{{ plugin.author }}</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无插件" />

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="`${currentPlugin?.icon || '🔌'} ${currentPlugin?.name}`"
      width="700px"
    >
      <template v-if="currentPlugin">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="作者">
            {{ currentPlugin.author }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            v{{ currentPlugin.version }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="pluginTypeTagType(currentPlugin.plugin_type)">
              {{ getPluginTypeLabel(currentPlugin.plugin_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="安装状态">
            <el-tag :type="currentPlugin.is_installed ? 'success' : 'info'">
              {{ currentPlugin.is_installed ? '已安装' : '未安装' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下载次数" :span="2">
            {{ currentPlugin.download_count }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentPlugin.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentPlugin.permissions?.length" label="权限" :span="2">
            <el-tag v-for="perm in currentPlugin.permissions" :key="perm" size="small" style="margin-right: 4px;">
              {{ perm }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 插件配置（已安装时显示） -->
        <div v-if="currentPlugin.is_installed" class="section">
          <h4>⚙️ 插件配置</h4>
          <el-form :model="pluginConfig" label-width="150px">
            <el-form-item v-for="(config, key) in pluginConfig" :key="key" :label="key">
              <el-input v-if="typeof config === 'string'" v-model="pluginConfig[key]" />
              <el-switch v-else-if="typeof config === 'boolean'" v-model="pluginConfig[key]" />
              <el-input-number v-else-if="typeof config === 'number'" v-model="pluginConfig[key]" />
            </el-form-item>
          </el-form>
        </div>
      </template>

      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button v-if="!currentPlugin?.is_installed" type="primary" @click="installPlugin" :loading="installing">
          <el-icon><Download /></el-icon>
          安装
        </el-button>
        <template v-else>
          <el-button @click="uninstallPlugin" :loading="uninstalling" type="danger">
            卸载
          </el-button>
          <el-button type="primary" @click="saveConfig" :loading="savingConfig">
            保存配置
          </el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh, Loading, Download, Star } from '@element-plus/icons-vue';
import {
  listPlugins,
  getPlugin,
  installPlugin as doInstall,
  uninstallPlugin as doUninstall,
  getPluginConfigs,
  setPluginConfig,
  type Plugin,
  type PluginInstallRequest
} from '../../api/plugin';

// 状态
const loading = ref(false);
const plugins = ref<Plugin[]>([]);
const detailVisible = ref(false);
const installing = ref(false);
const uninstalling = ref(false);
const savingConfig = ref(false);
const currentPlugin = ref<Plugin | null>(null);
const pluginConfig = reactive<Record<string, any>>({});

const filters = reactive({
  keyword: '',
  plugin_type: '',
  is_official: undefined as boolean | undefined,
  is_installed: undefined as boolean | undefined
});

// 插件类型映射
const PLUGIN_TYPE_LABELS: Record<string, string> = {
  'notification': '通知渠道',
  'executor': '任务执行器',
  'datasource': '数据源',
  'trigger': '触发器',
  'storage': '存储',
  'ai': 'AI引擎'
};

const PLUGIN_TYPE_TAGS: Record<string, string> = {
  'notification': 'primary',
  'executor': 'success',
  'datasource': 'warning',
  'trigger': 'danger',
  'storage': 'info',
  'ai': ''
};

function getPluginTypeLabel(type: string) {
  return PLUGIN_TYPE_LABELS[type] || type;
}

function pluginTypeTagType(type: string) {
  return PLUGIN_TYPE_TAGS[type] || 'info';
}

// 方法
async function loadPlugins() {
  loading.value = true;
  try {
    const res = await listPlugins(filters);
    plugins.value = res.data || res;
  } catch (e) {
    ElMessage.error('加载插件列表失败');
  } finally {
    loading.value = false;
  }
}

async function openDetail(plugin: Plugin) {
  currentPlugin.value = plugin;
  detailVisible.value = true;

  // 如果已安装，加载配置
  if (plugin.is_installed) {
    try {
      const res = await getPluginConfigs(plugin.plugin_id);
      const configs = res.data || res;
      Object.keys(pluginConfig).forEach(key => delete pluginConfig[key]);
      configs.forEach((c: any) => {
        pluginConfig[c.config_key] = c.config_value;
      });
    } catch (e) {
      ElMessage.error('加载插件配置失败');
    }
  }
}

async function installPlugin() {
  if (!currentPlugin.value) return;
  installing.value = true;
  try {
    const req: PluginInstallRequest = {
      plugin_id: currentPlugin.value.plugin_id,
      config: {}
    };
    await doInstall(req);
    ElMessage.success('安装成功');
    await loadPlugins();
    await openDetail(currentPlugin.value);
  } catch (e) {
    ElMessage.error('安装失败');
  } finally {
    installing.value = false;
  }
}

async function uninstallPlugin() {
  if (!currentPlugin.value) return;
  uninstalling.value = true;
  try {
    await doUninstall(currentPlugin.value.plugin_id);
    ElMessage.success('卸载成功');
    await loadPlugins();
    detailVisible.value = false;
  } catch (e) {
    ElMessage.error('卸载失败');
  } finally {
    uninstalling.value = false;
  }
}

async function saveConfig() {
  if (!currentPlugin.value) return;
  savingConfig.value = true;
  try {
    for (const [key, value] of Object.entries(pluginConfig)) {
      await setPluginConfig(currentPlugin.value.plugin_id, {
        config_key: key,
        config_value: String(value)
      });
    }
    ElMessage.success('配置保存成功');
  } catch (e) {
    ElMessage.error('配置保存失败');
  } finally {
    savingConfig.value = false;
  }
}

// 初始化
onMounted(() => {
  loadPlugins();
});
</script>

<style scoped lang="scss">
.plugin-market {
  padding: 20px;

  .header {
    margin-bottom: 24px;

    h2 {
      margin: 0 0 8px;
      font-size: 24px;
    }

    p {
      margin: 0;
      color: #666;
    }
  }

  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
  }

  .loading {
    text-align: center;
    padding: 60px 0;
    color: #999;
  }

  .plugin-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
  }

  .plugin-card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      border-color: #409eff;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;

      .icon {
        font-size: 24px;
      }

      .name {
        font-size: 16px;
        font-weight: 600;
        flex: 1;
      }

      .official-tag {
        font-size: 12px;
      }
    }

    .card-body {
      .description {
        font-size: 13px;
        color: #666;
        margin-bottom: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .meta {
        display: flex;
        gap: 8px;
        font-size: 12px;

        .plugin-type {
          padding: 2px 8px;
          border-radius: 4px;

          &.type-notification { background: #eff6ff; color: #2563eb; }
          &.type-executor { background: #ecfdf5; color: #059669; }
          &.type-datasource { background: #fffbeb; color: #d97706; }
          &.type-trigger { background: #fef2f2; color: #dc2626; }
          &.type-storage { background: #f0f9ff; color: #0284c7; }
          &.type-ai { background: #faf5ff; color: #9333ea; }
        }

        .version {
          color: #666;
        }
      }
    }

    .card-footer {
      display: flex;
      gap: 16px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;
      font-size: 12px;
      color: #999;

      > span {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .author {
        margin-left: auto;
      }
    }
  }

  .section {
    margin-top: 24px;

    h4 {
      margin: 0 0 12px;
      font-size: 14px;
      color: #333;
    }
  }
}
</style>
