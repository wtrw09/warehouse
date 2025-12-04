# 通用数据导入组件使用指南

## 概述

通用数据导入组件是一套完整的解决方案，支持Excel文件和粘贴数据的导入功能，适用于所有BASE管理模块（仓库、客户、供应商、货位等）。

## 组件架构

```
UniversalImport (通用导入容器)
├── ImportUploader (文件上传组件)
├── DataPreview (数据预览组件)
├── ValidationResult (验证结果组件)
├── ImportProgress (导入进度组件)
└── ImportResult (导入结果组件)
```

## 快速开始

### 1. 基本使用

```vue
<template>
  <div>
    <!-- 仓库数据导入 -->
    <UniversalImport
      :config="warehouseImportConfig"
      @import-completed="handleImportCompleted"
      @close="handleClose"
    />
  </div>
</template>

<script setup lang="ts">
import { UniversalImport, warehouseImportConfig } from '@/components/common/import';
import type { BatchImportResult } from '@/components/common/import';

const handleImportCompleted = (result: BatchImportResult) => {
  console.log('导入完成:', result);
  // 处理导入结果，如刷新列表等
};

const handleClose = () => {
  console.log('关闭导入组件');
  // 关闭导入界面
};
</script>
```

### 2. 在弹窗中使用

```vue
<template>
  <div>
    <el-button @click="showImportDialog = true">导入仓库数据</el-button>
    
    <el-dialog
      v-model="showImportDialog"
      title="仓库数据导入"
      width="80%"
      :close-on-click-modal="false"
    >
      <UniversalImport
        :config="warehouseImportConfig"
        @import-completed="handleImportCompleted"
        @close="showImportDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { UniversalImport, warehouseImportConfig } from '@/components/common/import';

const showImportDialog = ref(false);

const handleImportCompleted = (result: BatchImportResult) => {
  console.log('导入完成:', result);
  showImportDialog.value = false;
  // 刷新数据列表
  refreshWarehouseList();
};
</script>
```

### 3. 自定义配置使用

```vue
<template>
  <UniversalImport
    :config="customConfig"
    @import-completed="handleImportCompleted"
    @close="handleClose"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { UniversalImport } from '@/components/common/import';
import type { ImportConfig } from '@/components/common/import';

const customConfig = computed<ImportConfig>(() => ({
  entityName: '自定义实体',
  entityKey: 'custom',
  apiEndpoint: '/api/custom/batch-import',
  templateFields: [
    {
      key: 'name',
      label: '名称',
      required: true,
      type: 'string',
      maxLength: 100,
      example: '示例名称'
    },
    {
      key: 'description',
      label: '描述',
      required: false,
      type: 'string',
      maxLength: 200,
      example: '示例描述'
    }
  ],
  validationRules: [
    {
      field: 'name',
      type: 'required',
      message: '名称不能为空'
    }
  ],
  uniqueFields: ['name'],
  previewColumns: [
    { key: 'name', label: '名称', width: 150 },
    { key: 'description', label: '描述', width: 200 }
  ],
  batchImportAPI: async (data: any[]) => {
    // 自定义API调用
    const response = await fetch('/api/custom/batch-import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}));
</script>
```

## 配置说明

### ImportConfig 接口

```typescript
interface ImportConfig {
  entityName: string;              // 实体名称（如："仓库"、"客户"）
  entityKey: string;               // 实体键（如："warehouse"、"customer"）
  apiEndpoint: string;             // API端点
  templateFields: TemplateField[]; // 模板字段配置
  validationRules: ValidationRule[]; // 验证规则
  uniqueFields?: string[];         // 唯一性检查字段
  previewColumns: PreviewColumn[]; // 预览表格列配置
  batchImportAPI: (data: any[]) => Promise<BatchImportResult>;
  downloadTemplateAPI?: () => Promise<Blob>;
}
```

### 预定义配置

系统提供了以下预定义配置：

- `warehouseImportConfig` - 仓库导入配置
- `customerImportConfig` - 客户导入配置
- `supplierImportConfig` - 供应商导入配置
- `binImportConfig` - 货位导入配置

## 功能特性

### 1. 双重数据输入方式

- **Excel文件上传**：支持.xls和.xlsx格式，最大10MB
- **直接粘贴数据**：支持Tab分隔的文本数据，最多20条

### 2. 智能数据预览

- 大数据文件（>20条）只显示前20条预览
- 实时数据验证和错误高亮
- 支持错误数据的在线编辑

### 3. 多层级数据验证

- **客户端验证**：基础格式和长度验证
- **服务端验证**：业务规则和唯一性检查
- **重复性检查**：内部重复 + 数据库重复检查

### 4. 灵活的错误处理

- 智能编辑策略选择（在线编辑 vs 文件下载）
- 错误数据文件下载
- 详细的错误信息展示

### 5. 完整的导入流程

- 步骤式导入界面
- 实时进度追踪
- 详细的结果报告

## 集成到现有组件

### 在仓库管理组件中集成

```vue
<!-- WarehouseConfig.vue -->
<template>
  <div class="warehouse-config">
    <!-- 现有的仓库管理界面 -->
    <div class="warehouse-actions">
      <el-button type="primary" @click="showImportDialog = true">
        <el-icon><Upload /></el-icon>
        导入仓库数据
      </el-button>
    </div>
    
    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="仓库数据导入"
      width="80%"
      :close-on-click-modal="false"
    >
      <UniversalImport
        :config="warehouseImportConfig"
        @import-completed="handleWarehouseImportCompleted"
        @close="showImportDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { UniversalImport, warehouseImportConfig } from '@/components/common/import';

const showImportDialog = ref(false);

const handleWarehouseImportCompleted = (result: BatchImportResult) => {
  console.log('仓库导入完成:', result);
  showImportDialog.value = false;
  
  // 刷新仓库列表
  refreshWarehouseList();
  
  // 显示导入结果提示
  if (result.success_count > 0) {
    ElMessage.success(`成功导入${result.success_count}条仓库数据`);
  }
  if (result.error_count > 0) {
    ElMessage.warning(`${result.error_count}条数据导入失败，请检查错误信息`);
  }
};
</script>
```

## 注意事项

### 1. 依赖安装

确保项目中已安装必要的依赖：

```bash
npm install xlsx element-plus
```

### 2. 类型支持

在使用TypeScript时，确保正确导入类型：

```typescript
import type { 
  ImportConfig, 
  BatchImportResult, 
  ImportError 
} from '@/components/common/import';
```

### 3. API接口要求

后端API需要支持以下接口格式：

```typescript
// 批量导入接口
POST /api/{entity}/batch-import
Content-Type: application/json

// 请求体
{
  "data": [
    { "field1": "value1", "field2": "value2" },
    // ... 更多数据
  ]
}

// 响应体
{
  "total_count": 100,
  "success_count": 95,
  "error_count": 5,
  "errors": [
    {
      "row_index": 3,
      "field": "name",
      "error_message": "名称已存在",
      "raw_data": { "name": "重复名称" }
    }
  ],
  "import_time": "2024-01-20T10:30:00",
  "has_error_file": true,
  "error_file_url": "/api/download-error-file?id=123"
}
```

### 4. 权限控制

确保用户具有相应的导入权限（如BASE-edit权限）。

## 扩展和自定义

### 1. 添加新的实体配置

```typescript
// 在 importConfig.ts 中添加新配置
export const newEntityImportConfig: ImportConfig = {
  entityName: '新实体',
  entityKey: 'new_entity',
  // ... 其他配置
};

// 更新配置映射
export const importConfigs = {
  warehouse: warehouseImportConfig,
  customer: customerImportConfig,
  supplier: supplierImportConfig,
  bin: binImportConfig,
  new_entity: newEntityImportConfig // 新增
};
```

### 2. 自定义验证规则

```typescript
const customValidationRules: ValidationRule[] = [
  {
    field: 'email',
    type: 'format',
    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: '邮箱格式不正确'
  }
];
```

### 3. 自定义列格式化

```typescript
const customPreviewColumns: PreviewColumn[] = [
  {
    key: 'created_date',
    label: '创建日期',
    width: 120,
    formatter: (value) => new Date(value).toLocaleDateString()
  }
];
```

## 常见问题

### 1. SheetJS解析失败

确保Excel文件格式正确，第一行为标题行，数据从第二行开始。

### 2. 大文件上传超时

调整后端服务器的文件大小限制和请求超时时间。

### 3. 权限问题

确保用户具有对应实体的编辑权限。

### 4. 内存占用过高

对于超大数据文件，建议使用分批上传或服务端解析。

## 更新日志

- v1.0.0: 初始版本，支持基础导入功能
- v1.1.0: 添加粘贴数据功能
- v1.2.0: 优化大数据处理性能
- v1.3.0: 增强错误处理和用户体验