// 通用导入功能的TypeScript类型定义

export interface TemplateField {
  key: string;           // 字段键
  label: string;         // 显示标签
  required: boolean;     // 是否必填
  type: 'string' | 'number' | 'date' | 'boolean'; // 字段类型
  maxLength?: number;    // 最大长度
  placeholder?: string;  // 占位符
  example?: string;      // 示例值
}

export interface ValidationRule {
  field: string;         // 字段名
  type: 'required' | 'maxLength' | 'unique' | 'format'; // 验证类型
  value?: any;           // 验证值
  message: string;       // 错误消息
}

export interface PreviewColumn {
  key: string;           // 字段键
  label: string;         // 列标题
  width?: number;        // 列宽
  formatter?: (value: any) => string; // 格式化函数
}

export interface ImportOptions {
  forceImport?: boolean;     // 是否强制导入（包含错误数据）
  format?: 'json' | 'excel'; // 提交格式
  count?: number;            // 数据条数
}

export interface ImportConfig<T = any> {
  entityName: string;              // 实体名称（如："仓库"、"客户"、"供应商"）
  entityKey: string;               // 实体键（如："warehouse"、"customer"、"supplier"），也用作实体类型
  apiEndpoint: string;             // API端点（如："/api/warehouses/batch-import"）
  templateFields: TemplateField[]; // 模板字段配置
  validationRules: ValidationRule[]; // 验证规则
  uniqueFields?: string[];         // 唯一性检查字段
  previewColumns: PreviewColumn[]; // 预览表格列配置
  batchImportAPI: (data: T[] | Blob | FormData) => Promise<BatchImportResult>;
  downloadTemplateAPI?: () => Promise<Blob>;
  isExcelImport?: boolean;         // 是否为Excel导入的数据
  originalExcelFile?: File;        // 原始Excel文件（仅用于Excel导入）
}

export interface ImportError {
  row_index: number;     // 行号
  field: string;         // 字段名
  error_message: string; // 错误信息
  raw_data: any;         // 原始数据
}

export interface BatchImportResult {
  total_count: number;           // 总记录数
  success_count: number;         // 成功导入数
  error_count: number;           // 导入失败数
  errors: ImportError[];         // 错误详情
  import_time: string;           // 导入时间
  has_error_file: boolean;       // 是否有错误文件
  error_file_name?: string;      // 错误文件名
}

export interface ParsedData {
  data: any;             // 解析后的数据
  rowIndex: number;      // 行号
  source: 'file' | 'paste'; // 数据来源
}

export interface PreviewInfo {
  previewData: any[];    // 预览数据
  totalRows: number;     // 总行数
  previewRows: number;   // 预览行数
  hasMoreData: boolean;  // 是否有更多数据
  source: 'file' | 'paste'; // 数据来源
  isEditable: boolean;   // 是否支持在线编辑
  hasExceededLimit?: boolean; // 是否超过数据限制
}

export interface ImportProgress {
  current: number;       // 当前处理数量
  total: number;         // 总数量
  percentage: number;    // 百分比
  status: 'uploading' | 'parsing' | 'validating' | 'importing' | 'completed' | 'error';
  message: string;       // 进度消息
  success_count?: number; // 成功数量（实时更新）
  error_count?: number;   // 失败数量（实时更新）
  has_error_file?: boolean; // 是否生成了错误文件
  error_file_name?: string;  // 错误文件名
}

export interface EditStrategy {
  strategy: 'inline' | 'download' | 'choice';
  message: string;
  forceDownload?: boolean;
}

// 导入状态枚举
export enum ImportStatus {
  IDLE = 'idle',
  UPLOADING = 'uploading',
  PARSING = 'parsing',
  VALIDATING = 'validating',
  PREVIEWING = 'previewing',
  IMPORTING = 'importing',
  COMPLETED = 'completed',
  ERROR = 'error'
}

// 支持的文件类型
export const SUPPORTED_FILE_TYPES = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
];

// 文件大小限制（10MB）
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 粘贴数据最大行数
export const MAX_PASTE_ROWS = 20;