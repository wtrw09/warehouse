// 批次编码生成相关类型定义

/** 批次编码生成请求参数 */
export interface BatchCodeGenerateRequest {
  material_id: number;
  batch_date: string; // 日期格式: YYYY-MM-DD
}

/** 批次编码生成响应数据 */
export interface BatchCodeGenerateResponse {
  batch_code: string; // 生成的批次编码
  material_code: string; // 器材编码
  batch_date: string; // 日期
  sequence: number; // 流水号
}

/** 批次编码生成API响应类型别名 */
export type BatchCodeGenerateResponseType = BatchCodeGenerateResponse;