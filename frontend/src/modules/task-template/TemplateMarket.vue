<template>
  <div class="template-market">
    <div class="header">
      <h2>🎯 任务模板市场</h2>
      <p>一键导入常用任务，无需从零写脚本</p>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索模板名称或描述..."
        clearable
        style="width: 300px"
        @input="loadTemplates"
      />
      <el-select v-model="filters.category" placeholder="分类" clearable @change="loadTemplates">
        <el-option label="全部" value="" />
        <el-option label="系统运维类" value="系统运维类" />
        <el-option label="开发工具类" value="开发工具类" />
        <el-option label="个人助理类" value="个人助理类" />
        <el-option label="网络监控类" value="网络监控类" />
      </el-select>
      <el-select v-model="filters.difficulty" placeholder="难度" clearable @change="loadTemplates">
        <el-option label="全部" value="" />
        <el-option label="入门" value="入门" />
        <el-option label="中级" value="中级" />
        <el-option label="高级" value="高级" />
      </el-select>
      <el-button type="primary" @click="loadTemplates">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载中...
    </div>

    <!-- 模板列表 -->
    <div v-else-if="templates.length" class="template-grid">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        @click="openDetail(template)"
      >
        <div class="card-header">
          <span class="icon">{{ template.icon || '📦' }}</span>
          <span class="name">{{ template.name }}</span>
          <el-tag v-if="template.is_official" size="small" type="success" class="official-tag">官方</el-tag>
        </div>
        <div class="card-body">
          <p class="description">{{ template.description || '暂无描述' }}</p>
          <div class="meta">
            <span class="difficulty" :class="`difficulty-${template.difficulty}`">
              {{ template.difficulty }}
            </span>
            <span class="category">{{ template.category }}</span>
          </div>
        </div>
        <div class="card-footer">
          <span class="downloads">
            <el-icon><Download /></el-icon>
            {{ template.download_count }}
          </span>
          <span v-if="template.rating_avg" class="rating">
            <el-icon><Star /></el-icon>
            {{ template.rating_avg.toFixed(1) }}
          </span>
          <span class="author">{{ template.author }}</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无模板" />

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="`${currentTemplate?.icon || '📦'} ${currentTemplate?.name}`"
      width="800px"
    >
      <template v-if="currentTemplateDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="作者">
            {{ currentTemplateDetail.author }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            v{{ currentTemplateDetail.version }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ currentTemplateDetail.category }}
          </el-descriptions-item>
          <el-descriptions-item label="难度">
            <el-tag :type="difficultyType(currentTemplateDetail.difficulty)">
              {{ currentTemplateDetail.difficulty }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下载次数" :span="2">
            {{ currentTemplateDetail.download_count }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentTemplateDetail.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- Cron建议 -->
        <div v-if="currentTemplateDetail.cron_suggestions?.length" class="section">
          <h4>⏰ 推荐执行时间</h4>
          <el-radio-group v-model="selectedCron">
            <el-radio
              v-for="cron in currentTemplateDetail.cron_suggestions"
              :key="cron.id"
              :value="cron.cron_value"
            >
              {{ cron.label }} <el-tag size="small" type="info">{{ cron.cron_value }}</el-tag>
            </el-radio>
          </el-radio-group>
        </div>

        <!-- 参数配置表单（动态生成） -->
        <div v-if="currentTemplateDetail.schema" class="section">
          <h4>⚙️ 参数配置</h4>
          <el-form :model="formConfig" label-width="150px">
            <template
              v-for="(prop, propKey) in currentTemplateDetail.schema.schema_json.properties"
              :key="propKey"
            >
              <el-form-item :label="prop.title || propKey">
                <el-input
                  v-if="prop.type === 'string' && !prop.enum"
                  v-model="formConfig[propKey]"
                  :placeholder="prop.placeholder"
                  type="textarea"
                  :rows="prop.multiline ? 3 : 1"
                />
                <el-select v-else-if="prop.type === 'string' && prop.enum" v-model="formConfig[propKey]">
                  <el-option
                    v-for="(label, val) in (prop.enum_labels || {})"
                    :key="val"
                    :label="label"
                    :value="val"
                  />
                  <el-option
                    v-else
                    v-for="val in prop.enum"
                    :key="val"
                    :label="val"
                    :value="val"
                  />
                </el-select>
                <el-input-number
                  v-else-if="prop.type === 'number'"
                  v-model="formConfig[propKey]"
                  :min="prop.min"
                  :max="prop.max"
                />
                <el-switch v-else-if="prop.type === 'boolean'" v-model="formConfig[propKey]" />
              </el-form-item>
            </template>
          </el-form>
        </div>

        <!-- 脚本预览 -->
        <div v-if="currentTemplateDetail.script" class="section">
          <h4>📜 脚本预览</h4>
          <el-input
            :model-value="currentTemplateDetail.script.script_content"
            type="textarea"
            :rows="10"
            readonly
          />
        </div>
      </template>

      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" @click="openImportModal" :loading="importing">
          <el-icon><Upload /></el-icon>
          一键导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importVisible" title="导入模板" width="600px">
      <el-form :model="importForm" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="importForm.name" :placeholder="currentTemplate?.name" />
        </el-form-item>
        <el-form-item label="选择节点">
          <el-select v-model="importForm.node_id" placeholder="请选择节点">
            <!-- 这里对接真实的节点选择 -->
            <el-option label="本地节点" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行时间">
          <el-input v-model="importForm.schedule" placeholder="Cron表达式" />
          <div style="margin-top: 8px; color: #999; font-size: 12px;">
            例如：0 8 * * *（每天早上8点）
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="doImport" :loading="importing">
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh, Loading, Download, Star, Upload } from '@element-plus/icons-vue';
import {
  listTemplates,
  getTemplateDetail,
  importTemplate as doImportApi,
  type TaskTemplate,
  type TaskTemplateDetail,
  type TemplateImportRequest
} from '../../api/task-template';

// 状态
const loading = ref(false);
const templates = ref<TaskTemplate[]>([]);
const detailVisible = ref(false);
const importVisible = ref(false);
const importing = ref(false);
const currentTemplate = ref<TaskTemplate | null>(null);
const currentTemplateDetail = ref<TaskTemplateDetail | null>(null);
const selectedCron = ref('');
const formConfig = reactive<Record<string, any>>({});
const importForm = reactive<TemplateImportRequest>({
  template_id: '',
  node_id: 1,
  config: {},
  schedule: '',
  name: ''
});

const filters = reactive({
  keyword: '',
  category: '',
  difficulty: ''
});

// 方法
async function loadTemplates() {
  loading.value = true;
  try {
    const res = await listTemplates(filters);
    templates.value = res.data || res;
  } catch (e) {
    ElMessage.error('加载模板列表失败');
  } finally {
    loading.value = false;
  }
}

async function openDetail(template: TaskTemplate) {
  currentTemplate.value = template;
  detailVisible.value = true;
  try {
    const res = await getTemplateDetail(template.template_id);
    currentTemplateDetail.value = res.data || res;

    // 初始化默认配置
    if (currentTemplateDetail.value.schema?.schema_json?.properties) {
      Object.keys(currentTemplateDetail.value.schema.schema_json.properties).forEach((key) => {
        const prop = currentTemplateDetail.value!.schema!.schema_json.properties[key];
        formConfig[key] = prop.default !== undefined ? prop.default : (prop.type === 'boolean' ? false : '');
      });
    }

    // 初始化默认Cron
    if (currentTemplateDetail.value.cron_suggestions?.length) {
      const defaultCron = currentTemplateDetail.value.cron_suggestions.find(c => c.is_default);
      selectedCron.value = defaultCron?.cron_value || currentTemplateDetail.value.cron_suggestions[0].cron_value;
    }
  } catch (e) {
    ElMessage.error('加载模板详情失败');
  }
}

function openImportModal() {
  importForm.template_id = currentTemplate.value!.template_id;
  importForm.name = currentTemplate.value!.name;
  importForm.schedule = selectedCron.value;
  importForm.config = { ...formConfig };
  importVisible.value = true;
}

async function doImport() {
  if (!importForm.node_id) {
    ElMessage.warning('请选择节点');
    return;
  }
  if (!importForm.schedule) {
    ElMessage.warning('请输入Cron表达式');
    return;
  }

  importing.value = true;
  try {
    const res = await doImportApi(importForm);
    ElMessage.success('导入成功！');
    importVisible.value = false;
    detailVisible.value = false;
    // 刷新下载次数
    await loadTemplates();
  } catch (e) {
    ElMessage.error('导入失败');
  } finally {
    importing.value = false;
  }
}

function difficultyType(difficulty: string) {
  const map: Record<string, any> = {
    '入门': 'success',
    '中级': 'warning',
    '高级': 'danger'
  };
  return map[difficulty] || 'info';
}

// 初始化
onMounted(() => {
  loadTemplates();
});
</script>

<style scoped lang="scss">
.template-market {
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

  .template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }

  .template-card {
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

        .difficulty {
          padding: 2px 8px;
          border-radius: 4px;

          &.difficulty-入门 { background: #f0f9ff; color: #0284c7; }
          &.difficulty-中级 { background: #fffbeb; color: #d97706; }
          &.difficulty-高级 { background: #fef2f2; color: #dc2626; }
        }

        .category {
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
