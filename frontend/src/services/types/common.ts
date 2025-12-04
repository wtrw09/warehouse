// 通用分页参数接口
export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_field?: string;
  sort_asc?: boolean;
}

// 通用分页结果接口
export interface PaginationResult<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: T[];
}