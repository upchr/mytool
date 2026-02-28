<template>
  <n-card title="DNS授权">
    <n-space justify="end" style="margin-bottom: 10px">
      <n-button type="primary" @click="showDialog=true;dialogType='add';formData=defaultFormData">添加授权</n-button>
      <n-button type="error" @click="deleteAll">批量删除</n-button>
    </n-space>
    <n-p>你选中了 {{ checkedRowKeys.length }} 行。</n-p>
    <n-data-table
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        :pagination="pagination"
        :bordered="false"
    />


    <DialogForm
        ref="dialogRef"
        dialogPreset="card"
        v-model:visible="showDialog"
        v-model:formData="formData"
        :use-field-groups="true"
        :field-groups="fieldGroups"
        :rules="formRules"
        :title="dialogTitle(formData.name)"
        :positive-text="dialogType === 'add' ? '添加' : '更新'"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="设置已保存！"
        @submit="handleSubmit"
        @field-change="handleFieldChange"
    >
      <template #action="{ formData }">
        <!--modal预设为dialog不要用action，会覆盖默认positive-click，negative-click对应触发@submit="handleSubmit"，@cancel="handleCancel"-->
        <!--覆盖后，提交需要自己验证表单handleSubmit(formData,true)-->
        <!--未覆盖，子组件自行验证表单后emit-handleSubmit(formData)-->
        <!--获取子组件值formData：<slot name="action" :formData="localFormData"/>-->
        <n-space justify="end">
          <n-button size="small" type="default" @click="handleCancel">取消</n-button>
          <n-button size="small" type="success" @click="handleSubmit(formData,true)">确定</n-button>
        </n-space>
      </template>
    </DialogForm>
  </n-card>

</template>

<script setup>
import {NButton, NTag, useMessage} from "naive-ui";
import {h, ref} from "vue";
import DialogForm from "@/components/DialogForm.vue";
import {resetPassword} from "@/utils/auth.js";
const message = useMessage();

const checkedRowKeys = ref([]);

const pagination = {pageSize: 10};

function createColumns({actions }) {
  return [
    {
      type: "selection",
      fixed: "left"
    },
    {
      title: "ID",
      key: "id",
      width: 100,
      fixed: "left"
    },
    {
      title: "Name",
      key: "name",
      width: 200,
      fixed: "left"
    },
    {
      title: "Type",
      key: "type",
      render(row, index) {
        return h("span", ["row ", index]);
      }
    },
    {
      title: "Tags",
      key: "tags",
      render(row) {
        const tags = row.tags.map((tagKey) => {
          return h(
              NTag,
              {
                style: {
                  marginRight: "6px"
                },
                type: "info",
                bordered: false
              },
              {
                default: () => tagKey
              }
          );
        });
        return tags;
      }
    },
    {
      title: "Action",
      key: "actions",
      render(row) {
        return h('div', { style: { display: 'flex', gap: '8px' } }, [
          // 编辑按钮
          h(
              NButton,
              {
                strong: true,
                type: "primary",
                tertiary: true,
                size: "small",
                onClick: () => actions.edit(row)
              },
              { default: () => "编辑" }
          ),
          // 删除按钮
          h(
              NButton,
              {
                strong: true,
                type: "error",
                tertiary: true,
                size: "small",
                onClick: () => actions.delete(row)
              },
              { default: () => "删除" }
          )
        ]);
      }
    }
  ];
}
const columns = createColumns({
  actions: {
    edit: (row) => {
      window.$message.info(`编辑 ${row.name}`);
      // 处理编辑逻辑
      showDialog.value=true;
      dialogType.value='edit'

      formData.value.name=row.name

    },
    delete: (row) => {
      window.$message.error(`删除 ${row.name}`);
      // 处理删除逻辑
    }
  }
});

const data = Array.from({length: 46}).map((_, index) => ({
  key: index+1,
  id: index+1,
  name: `Edward King ${index}`,
  tags: [index,index%2==0?'ou':'ji']
}));

const deleteAll = async () => {
  if (checkedRowKeys.value.length === 0) return

  try {
    console.log(checkedRowKeys.value)
    // await window.$request.post('/notes/deleteBatch', { note_ids: selectedNoteIds.value })
    window.$message.success(`成功删除 ${checkedRowKeys.value.length} 个节点`)
    // cancelBatch()
    // await loadNotes()
  } catch (error) {
    window.$message.error('批量删除失败')
  }
}


//////////新增、编辑对话框
const dialogRef = ref(null)//action按钮表单要调用dialogRef.validate子组件验证
// 表单数据
const formData = ref({
  name: '',
  type: 'tencent',
  secretId: '',
  secretKey: '',
})
const defaultFormData = ref({
  name: '',
  type: 'tencent',
  secretId: '',
  secretKey: '',
})
// 字段分组配置
const fieldGroups = [
  {
    title: 'DNS厂商',
    fields: [
      {
        name: 'type',
        label: '类型',
        type: 'select',
        options: [
          { label: '腾讯云', value: 'tencent' },
          { label: '阿里云', value: 'alibaba' },
          { label: '其他', value: 'others' }
        ]
      }
    ]
  },
  {
    title: '配置信息',
    fields: [
      {
        name: 'name',
        label: '名称',
        type: 'input',
        placeholder: '请输入名称',
      },
      {
        name: 'secretId',
        label: 'secretId',
        type: 'input',
        placeholder: '请输入secretId',
      },
      {
        name: 'secretKey',
        label: 'secretKey',
        type: 'input',
        inputType:"password",
        showPasswordOn:"click",
        placeholder: '请输入secretKey',
      }
    ]
  }
]
// 验证规则
const formRules = (model) => ({
  type: [
    { required: true, message: '请选择类型', trigger: ['blur'] },
  ],
  name: [
    { required: true, message: '请输入名称', trigger: ['blur'] },
  ],
  secretId: [
    { required: true, message: '请输入secretId', trigger: ['blur'] },
  ],
  secretKey: [
    { required: true, message: '请输入secretKey', trigger: ['blur'] },
  ]
})

const showDialog = ref(false)

const dialogType = ref('add') // 'add' | 'edit'

const dialogTitle = (name) => {
  return dialogType.value === 'add' ? '添加' : '更新'+name
}

const handleCancel = () => {
  console.log('用户取消')
  showDialog.value=false//控制隐藏，card模式使用
}
// 处理提交
const handleSubmit = async (data,flag=false) => {
  if(flag){//自定义按钮时，验证表单
    if (dialogRef.value) {
      try {
        await dialogRef.value.validate()
        console.log('✅ 表单验证通过')
      } catch (error) {
        console.log('❌ 表单验证失败:', error)
        return
      }
    }
  }

  formData.value={...data}

  try {
    await resetPassword(data.oldPassword,data.newPassword)
    showDialog.value=false//控制隐藏，card模式使用
    // 刷新列表
  } catch (error) {
    console.log(error)
  }
}

// 字段变更监听（用于联动）
const handleFieldChange = ({ fieldName, value }) => {
/*  console.log(`字段 ${fieldName} 变化:`, {
    值: value,
    类型: typeof value,
    是否为数字: !isNaN(Number(value))
  })*/
}
//////////
</script>
