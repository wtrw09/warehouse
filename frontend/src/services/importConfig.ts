// 通用导入配置文件，定义各实体的导入配置

import { ImportConfig, BatchImportResult } from './types/import';
import { supplierAPI } from './base/supplier';
import { binApi } from './base/bin';
import { warehouseAPI } from './base/warehouse';
import { customerAPI } from './base/customer';

// 仓库服务 - 实际实现
const warehouseService = {
  batchImport: async (data: any[] | Blob | FormData): Promise<BatchImportResult> => {
    // 如果是FormData（Excel文件上传），直接调用后端API
    if (data instanceof FormData) {
      const response = await warehouseAPI.batchImportWarehouses(data);
      return response;
    }
    // 如果是Blob（文件），包装成FormData
    if (data instanceof Blob) {
      const formData = new FormData();
      formData.append('file', data);
      const response = await warehouseAPI.batchImportWarehouses(formData);
      return response;
    }
    // 如果是数组（JSON数据），直接调用批量导入API
    const response = await warehouseAPI.batchImportWarehouses(data);
    return response;
  },
  downloadTemplate: async (): Promise<Blob> => {
    return await warehouseAPI.downloadWarehouseTemplate();
  }
};
// 客户服务 - 实际实现
const customerService = {
  batchImport: async (data: any[] | Blob | FormData): Promise<BatchImportResult> => {
    // 如果是FormData（Excel文件上传），直接调用后端API
    if (data instanceof FormData) {
      const response = await customerAPI.batchImportCustomers(data);
      return response;
    }
    // 如果是Blob（文件），包装成FormData
    if (data instanceof Blob) {
      const formData = new FormData();
      formData.append('file', data);
      const response = await customerAPI.batchImportCustomers(formData);
      return response;
    }
    // 如果是数组（JSON数据），直接调用批量导入API
    const response = await customerAPI.batchImportCustomers(data);
    return response;
  },
  downloadTemplate: async (): Promise<Blob> => {
    return await customerAPI.downloadCustomerTemplate();
  }
};
// 货位服务 - 实际实现
const binService = {
  batchImport: async (data: any[] | Blob | FormData): Promise<BatchImportResult> => {
    // 如果是FormData（Excel文件上传），直接调用后端API
    if (data instanceof FormData) {
      const response = await binApi.batchImport(data);
      return response.data;
    }
    // 如果是Blob（文件），包装成FormData
    if (data instanceof Blob) {
      const formData = new FormData();
      formData.append('file', data);
      const response = await binApi.batchImport(formData);
      return response.data;
    }
    // 如果是数组（JSON数据），直接调用批量导入API
    const response = await binApi.batchImport(data);
    return response.data;
  },
  downloadTemplate: async (): Promise<Blob> => {
    return await binApi.downloadTemplate();
  }
};

// 供应商服务 - 实际实现
const supplierService = {
  batchImport: async (data: any[] | Blob | FormData): Promise<BatchImportResult> => {
    // 如果是FormData（Excel文件上传），直接调用后端API
    if (data instanceof FormData) {
      const response = await supplierAPI.batchImportSuppliers(data);
      return response;
    }
    // 如果是Blob（文件），包装成FormData
    if (data instanceof Blob) {
      const formData = new FormData();
      formData.append('file', data);
      const response = await supplierAPI.batchImportSuppliers(formData);
      return response;
    }
    // 如果是数组（JSON数据），直接调用批量导入API
    const response = await supplierAPI.batchImportSuppliers(data);
    return response;
  },
  downloadTemplate: async (): Promise<Blob> => {
    return await supplierAPI.downloadSupplierTemplate();
  }
};

// 仓库导入配置
export const warehouseImportConfig: ImportConfig = {
  entityName: '仓库',
  entityKey: 'warehouse',
  apiEndpoint: '/api/warehouses/batch-import',
  templateFields: [
    {
      key: 'warehouse_name',
      label: '仓库名',
      required: true,
      type: 'string',
      maxLength: 100,
      placeholder: '请输入仓库名',
      example: '上海中心仓库'
    },
    {
      key: 'warehouse_city',
      label: '所在城市',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入所在城市',
      example: '上海'
    },
    {
      key: 'warehouse_address',
      label: '详细地址',
      required: false,
      type: 'string',
      maxLength: 200,
      placeholder: '请输入详细地址',
      example: '浦东新区张江高科技园区'
    },
    {
      key: 'warehouse_manager',
      label: '负责人',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入负责人姓名',
      example: '张三'
    },
    {
      key: 'warehouse_contact',
      label: '联系方式',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入联系方式',
      example: '13800138000'
    }
  ],
  validationRules: [
    {
      field: 'warehouse_name',
      type: 'required',
      message: '仓库名不能为空'
    },
    {
      field: 'warehouse_name',
      type: 'maxLength',
      value: 100,
      message: '仓库名长度不能超过100个字符'
    },
    {
      field: 'warehouse_name',
      type: 'unique',
      message: '仓库名已存在'
    }
  ],
  uniqueFields: ['warehouse_name'],
  previewColumns: [
    { key: 'warehouse_name', label: '仓库名', width: 150 },
    { key: 'warehouse_city', label: '所在城市', width: 120 },
    { key: 'warehouse_address', label: '详细地址', width: 200 },
    { key: 'warehouse_manager', label: '负责人', width: 100 },
    { key: 'warehouse_contact', label: '联系方式', width: 150 }
  ],
  batchImportAPI: warehouseService.batchImport,
  downloadTemplateAPI: warehouseService.downloadTemplate
};

// 客户导入配置
export const customerImportConfig: ImportConfig = {
  entityName: '客户',
  entityKey: 'customer',
  apiEndpoint: '/api/customers/batch-import',
  templateFields: [
    {
      key: 'customer_name',
      label: '客户名称',
      required: true,
      type: 'string',
      maxLength: 100,
      placeholder: '请输入客户名称',
      example: '上海科技有限公司'
    },
    {
      key: 'customer_city',
      label: '所在城市',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入所在城市',
      example: '上海'
    },
    {
      key: 'customer_address',
      label: '地址',
      required: false,
      type: 'string',
      maxLength: 200,
      placeholder: '请输入地址',
      example: '上海市浦东新区张江高科技园区'
    },
    {
      key: 'customer_contact',
      label: '联系方式',
      required: false,
      type: 'string',
      maxLength: 20,
      placeholder: '请输入联系方式',
      example: '13800138000'
    },
    {
      key: 'customer_manager',
      label: '负责人',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入负责人姓名',
      example: '张三'
    }
  ],
  validationRules: [
    {
      field: 'customer_name',
      type: 'required',
      message: '客户名称不能为空'
    },
    {
      field: 'customer_name',
      type: 'maxLength',
      value: 100,
      message: '客户名称长度不能超过100个字符'
    },
    {
      field: 'customer_name',
      type: 'unique',
      message: '客户名称已存在'
    }
  ],
  uniqueFields: ['customer_name'],
  previewColumns: [
    { key: 'customer_name', label: '客户名称', width: 150 },
    { key: 'customer_city', label: '所在城市', width: 120 },
    { key: 'customer_address', label: '地址', width: 200 },
    { key: 'customer_contact', label: '联系方式', width: 120 },
    { key: 'customer_manager', label: '负责人', width: 100 }
  ],
  batchImportAPI: customerService.batchImport,
  downloadTemplateAPI: customerService.downloadTemplate
};

// 供应商导入配置
export const supplierImportConfig: ImportConfig = {
  entityName: '供应商',
  entityKey: 'supplier',
  apiEndpoint: '/api/suppliers/batch-import',
  templateFields: [
    {
      key: 'supplier_name',
      label: '供应商名称',
      required: true,
      type: 'string',
      maxLength: 100,
      placeholder: '请输入供应商名称',
      example: '北京物流有限公司'
    },
    {
      key: 'supplier_city',
      label: '所在城市',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入所在城市',
      example: '北京'
    },
    {
      key: 'supplier_address',
      label: '详细地址',
      required: false,
      type: 'string',
      maxLength: 200,
      placeholder: '请输入详细地址',
      example: '朝阳区建国门外大街'
    },
    {
      key: 'supplier_manager',
      label: '负责人',
      required: false,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入负责人姓名',
      example: '王五'
    },
    {
      key: 'supplier_contact',
      label: '联系方式',
      required: false,
      type: 'string',
      maxLength: 20,
      placeholder: '请输入联系电话',
      example: '010-87654321'
    }
  ],
  validationRules: [
    {
      field: 'supplier_name',
      type: 'required',
      message: '供应商名称不能为空'
    },
    {
      field: 'supplier_name',
      type: 'maxLength',
      value: 100,
      message: '供应商名称长度不能超过100个字符'
    },
    {
      field: 'supplier_name',
      type: 'unique',
      message: '供应商名称已存在'
    }
  ],
  uniqueFields: ['supplier_name'],
  previewColumns: [
    { key: 'supplier_name', label: '供应商名称', width: 150 },
    { key: 'supplier_city', label: '所在城市', width: 120 },
    { key: 'supplier_address', label: '详细地址', width: 200 },
    { key: 'supplier_manager', label: '负责人', width: 100 },
    { key: 'supplier_contact', label: '联系方式', width: 150 }
  ],
  batchImportAPI: supplierService.batchImport,
  downloadTemplateAPI: supplierService.downloadTemplate
};

// 货位导入配置
export const binImportConfig: ImportConfig = {
  entityName: '货位',
  entityKey: 'bin',
  apiEndpoint: '/api/bins/batch-import',
  templateFields: [
    {
      key: 'bin_code',
      label: '货位编码',
      required: true,
      type: 'string',
      maxLength: 50,
      placeholder: '请输入货位编码',
      example: 'A01-01-01'
    },
    {
      key: 'bin_name',
      label: '货位名称',
      required: false,
      type: 'string',
      maxLength: 100,
      placeholder: '请输入货位名称',
      example: 'A区第1排第1层第1位'
    },
    {
      key: 'warehouse_id',
      label: '所属仓库ID',
      required: true,
      type: 'number',
      placeholder: '请输入仓库ID',
      example: '1'
    },
    {
      key: 'description',
      label: '描述',
      required: false,
      type: 'string',
      maxLength: 200,
      placeholder: '请输入货位描述',
      example: '存放小件商品'
    }
  ],
  validationRules: [
    {
      field: 'bin_code',
      type: 'required',
      message: '货位编码不能为空'
    },
    {
      field: 'bin_code',
      type: 'maxLength',
      value: 50,
      message: '货位编码长度不能超过50个字符'
    },
    {
      field: 'bin_code',
      type: 'unique',
      message: '货位编码已存在'
    },
    {
      field: 'warehouse_id',
      type: 'required',
      message: '所属仓库不能为空'
    }
  ],
  uniqueFields: ['bin_code'],
  previewColumns: [
    { key: 'bin_code', label: '货位编码', width: 120 },
    { key: 'bin_name', label: '货位名称', width: 150 },
    { key: 'warehouse_id', label: '所属仓库ID', width: 100 },
    { key: 'description', label: '描述', width: 200 }
  ],
  batchImportAPI: binService.batchImport,
  downloadTemplateAPI: binService.downloadTemplate
};

// 导入配置映射
export const importConfigs = {
  warehouse: warehouseImportConfig,
  customer: customerImportConfig,
  supplier: supplierImportConfig,
  bin: binImportConfig
};

// 根据实体类型获取导入配置
export function getImportConfig(entityType: string): ImportConfig | null {
  return importConfigs[entityType as keyof typeof importConfigs] || null;
}

// 获取所有支持导入的实体类型
export function getSupportedEntityTypes(): string[] {
  return Object.keys(importConfigs);
}

// 导出服务对象
export { customerService };