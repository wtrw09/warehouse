import { PaginationParams, PaginationResult } from './common';

// 器材编码分类层级管理相关类型
export interface MaterialCodeLevelResponse {
  id: number;
  level_code: string;
  level_name: string;
  code: string;
  description?: string;
}

export interface MaterialCodeLevelCreate {
  level_code: string;
  level_name: string;
  code: string;
  description?: string;
}

export interface MaterialCodeLevelUpdate {
  level_code?: string;
  level_name?: string;
  code?: string;
  description?: string;
}

export interface MaterialCodeLevelQueryParams extends PaginationParams {
  search?: string;
  level_code?: string;
  level_name?: string;
}

export interface MaterialCodeLevelPaginationResult extends PaginationResult<MaterialCodeLevelResponse> {}

export interface BatchMaterialCodeLevelDelete {
  ids: number[];
}

export interface MaterialCodeLevelStatistics {
  total_count: number;
  level_count_by_depth: {
    [depth: number]: number;
  };
}

// 添加描述到器材编码分类层级请求类型
export interface MaterialCodeLevelAddDescription {
  level_code: string;
  description: string;
}

// 添加描述到器材编码分类层级响应类型
export interface MaterialCodeLevelAddDescriptionResult {
  message: string;
  level_code: string;
  new_description_list: string[];
}