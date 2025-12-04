# 通用导入组件职责分工说明

## 📋 组件架构概览

```
通用数据导入功能 (import/)
├── 🎯 核心组件
│   ├── UniversalImport.vue     # 流程协调器
│   ├── ImportUploader.vue      # 数据上传
│   ├── DataPreview.vue         # 数据预览
│   ├── ValidationResult.vue    # 验证结果
│   ├── ImportProgress.vue      # 导入进度
│   └── ImportResult.vue        # 结果展示
├── 📁 配置 & 类型
│   └── index.ts               # 组件导出
└── 📚 文档
    ├── README.md              # 详细文档
    └── *.md                   # 功能说明
```

## 🎯 核心组件职责

### 1. **UniversalImport.vue** - 流程协调器
- **职责**: 整体流程控制和状态管理
- **功能**: 步骤指示器、组件编排、事件协调
- **关系**: 父组件，管理所有子组件的生命周期

### 2. **ImportUploader.vue** - 数据上传
- **职责**: 文件上传和数据解析
- **功能**: Excel文件上传、文本粘贴、数据格式转换
- **输出**: ParsedData[] 解析后的数据

### 3. **DataPreview.vue** - 数据预览 + 前端验证
- **职责**: 数据表格展示、实时前端验证、错误标记
- **功能**: 
  - ✅ 预览前20条数据、字段映射
  - ✅ **前端验证**：必填验证、长度验证、格式验证、类型验证
  - ✅ 实时错误高亮和提示图标
  - ✅ 验证统计信息展示（有效/错误数量）
  - ✅ 内部重复数据检查
- **特点**: 承担客户端验证职责，实时反馈验证结果

### 4. **ValidationResult.vue** - 后端验证结果处理
- **职责**: 后端验证结果展示和错误处理
- **功能**: 
  - ✅ **后端验证**：业务规则、唯一性检查、数据库验证
  - ✅ 验证失败：提供在线编辑和错误文件下载
  - ✅ 验证通过：显示成功状态和开始导入按钮
  - ✅ 强制导入功能（包含错误数据的导入）
- **特点**: 专门处理服务端验证，接收DataPreview的前端验证结果

### 5. **ImportProgress.vue** - 导入进度
- **职责**: 实时进度展示和过程监控
- **功能**: 进度条、实时统计、简单完成提示
- **特点**: 专注进度，不展示详细结果

### 6. **ImportResult.vue** - 结果展示
- **职责**: 详细结果展示和后续操作
- **功能**: 完整统计、错误详情、操作按钮、导入日志
- **特点**: 唯一的结果展示页面

## 🔄 数据流向 + 验证分层

```
文件/文本输入 → ImportUploader → ParsedData[]
                      ↓
              DataPreview (前端验证)
                      ↓ 发送到后端
           ValidationResult (后端验证)
                      ↓ 验证通过
               ImportProgress (执行)
                      ↓
               ImportResult (结果)
```

### 🛡️ 验证分层架构

```
📊 DataPreview.vue        ← 前端验证层
├── 必填字段验证
├── 数据长度验证  
├── 数据格式验证
├── 数据类型验证
└── 内部重复检查

🔍 ValidationResult.vue   ← 后端验证层  
├── 业务规则验证
├── 数据库唯一性验证
├── 跨表关联验证
└── 复杂业务逻辑验证
```

## 📏 设计原则

### ✅ 单一职责
- 每个组件专注一个核心功能
- 避免功能重叠和职责模糊

### ✅ 避免重复
- 结果展示仅在 ImportResult 组件
- 前端验证仅在 DataPreview 组件  
- 后端验证仅在 ValidationResult 组件
- 错误文件下载统一使用 errorHandling 服务

### ✅ 松耦合
- 通过事件通信，组件间依赖最小
- 配置驱动，支持多种业务场景

## 🎛️ 配置化使用

所有组件通过 `ImportConfig` 配置驱动：
- 实体名称、字段定义、验证规则
- API接口、权限控制、样式配置
- 参考: `services/types/import.ts`

## 📝 使用示例

```vue
<template>
  <UniversalImport 
    :config="supplierImportConfig"
    @import-completed="handleImportCompleted"
    @close="closeDialog"
  />
</template>
```

> 配置文件参考: `services/importConfig.ts`