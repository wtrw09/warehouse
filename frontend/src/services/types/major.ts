// 专业管理相关类型
export interface MajorResponse {
  id: number;
  major_name: string;
  major_code: string;
  creator: string;
  create_time: string;
  update_time: string;
}

export interface MajorCreate {
  id?: number;
  major_name: string;
  major_code?: string;
  creator?: string;
}

export interface MajorUpdate {
  major_name?: string;
  major_code?: string;
}

export interface MajorQueryParams {
  search?: string;
}

export interface MajorListResult {
  data: MajorResponse[];
}

export interface BatchMajorDelete {
  major_ids: number[];
}