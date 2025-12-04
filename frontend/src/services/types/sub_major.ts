// 二级专业管理相关类型
export interface SubMajorResponse {
  id: number;
  sub_major_name: string;
  sub_major_code: string;
  description?: string;
  major_id?: number;
  major_name?: string;
  reserved?: string;
  creator?: string;
  create_time?: string;
  update_time?: string;
}

export interface SubMajorCreate {
  sub_major_name: string;
  sub_major_code?: string;
  description?: string; // JSON字符串格式，存储描述标签数组，如：["标签1","标签2"]
  major_id?: number;
}

export interface SubMajorUpdate {
  sub_major_name?: string;
  sub_major_code?: string;
  description?: string; // JSON字符串格式，存储描述标签数组，如：["标签1","标签2"]
  major_id?: number;
}

export interface SubMajorQueryParams {
  search?: string;
  major_id?: number;
}

export interface SubMajorListResult {
  data: SubMajorResponse[];
  total: number;
}

export interface BatchSubMajorDelete {
  sub_major_ids: number[];
}

export interface SubMajorStatistics {
  total_count: number;
  major_distribution: Record<string, number>;
}

// 添加二级专业描述相关类型
export interface SubMajorAddDescription {
  sub_major_id: number;
  description: string;
}

export interface SubMajorAddDescriptionResult {
  message: string;
  sub_major_id: number;
  new_description_list: string[];
}