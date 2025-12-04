// 通用导入组件入口文件

// 导出所有组件
export { default as UniversalImport } from './UniversalImport.vue';
export { default as ImportUploader } from './ImportUploader.vue';
export { default as DataPreview } from './DataPreview.vue';
export { default as ValidationResult } from './ValidationResult.vue';
export { default as ImportProgress } from './ImportProgress.vue';
export { default as ImportResult } from './ImportResult.vue';

// 导出类型定义
export type {
  ImportConfig,
  TemplateField,
  ValidationRule,
  PreviewColumn,
  ImportError,
  BatchImportResult,
  ParsedData,
  PreviewInfo,
  ImportProgress as IImportProgress,
  EditStrategy
} from '@/services/types/import';

// 导出配置
export {
  warehouseImportConfig,
  customerImportConfig,
  supplierImportConfig,
  binImportConfig,
  importConfigs,
  getImportConfig,
  getSupportedEntityTypes
} from '@/services/importConfig';

// 导出常量
export {
  SUPPORTED_FILE_TYPES,
  MAX_FILE_SIZE,
  MAX_PASTE_ROWS
} from '@/services/types/import';