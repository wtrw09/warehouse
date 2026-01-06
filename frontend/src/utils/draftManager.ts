/**
 * 草稿管理工具类
 * 用于在 LocalStorage 中保存和恢复用户输入的草稿数据
 */

const DRAFT_VERSION = '1.0';

/**
 * 草稿数据接口
 */
export interface DraftData<T = any> {
  version: string;      // 版本号，用于兼容性检查
  timestamp: string;    // 保存时间
  data: T;             // 实际数据
}

/**
 * 保存草稿到 LocalStorage
 * @param key - 草稿的唯一标识键
 * @param data - 要保存的数据
 * @returns 保存是否成功
 */
export function saveDraft<T>(key: string, data: T): boolean {
  try {
    const draftData: DraftData<T> = {
      version: DRAFT_VERSION,
      timestamp: new Date().toISOString(),
      data
    };
    
    localStorage.setItem(key, JSON.stringify(draftData));
    return true;
  } catch (error) {
    // LocalStorage 写入失败（可能空间不足或被禁用）
    console.error('保存草稿失败:', error);
    return false;
  }
}

/**
 * 从 LocalStorage 加载草稿
 * @param key - 草稿的唯一标识键
 * @returns 草稿数据，如果不存在或版本不匹配则返回 null
 */
export function loadDraft<T>(key: string): T | null {
  try {
    const draftJson = localStorage.getItem(key);
    if (!draftJson) {
      return null;
    }
    
    const draftData: DraftData<T> = JSON.parse(draftJson);
    
    // 版本检查：如果版本不匹配，清除旧草稿
    if (draftData.version !== DRAFT_VERSION) {
      console.warn('草稿版本不匹配，已清除旧草稿');
      clearDraft(key);
      return null;
    }
    
    return draftData.data;
  } catch (error) {
    // JSON 解析失败或其他错误
    console.error('加载草稿失败:', error);
    // 清除损坏的草稿数据
    clearDraft(key);
    return null;
  }
}

/**
 * 清除指定的草稿
 * @param key - 草稿的唯一标识键
 */
export function clearDraft(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('清除草稿失败:', error);
  }
}

/**
 * 检查是否存在指定的草稿
 * @param key - 草稿的唯一标识键
 * @returns 是否存在草稿
 */
export function hasDraft(key: string): boolean {
  try {
    const draftJson = localStorage.getItem(key);
    if (!draftJson) {
      return false;
    }
    
    // 检查是否可以正常解析
    const draftData: DraftData = JSON.parse(draftJson);
    
    // 版本检查
    if (draftData.version !== DRAFT_VERSION) {
      clearDraft(key);
      return false;
    }
    
    return true;
  } catch (error) {
    // JSON 解析失败，清除损坏的数据
    clearDraft(key);
    return false;
  }
}

/**
 * 获取草稿的保存时间
 * @param key - 草稿的唯一标识键
 * @returns 保存时间字符串，如果不存在则返回 null
 */
export function getDraftTimestamp(key: string): string | null {
  try {
    const draftJson = localStorage.getItem(key);
    if (!draftJson) {
      return null;
    }
    
    const draftData: DraftData = JSON.parse(draftJson);
    return draftData.timestamp;
  } catch (error) {
    console.error('获取草稿时间戳失败:', error);
    return null;
  }
}

/**
 * 格式化时间戳为可读格式
 * @param timestamp - ISO 格式的时间戳
 * @returns 格式化后的时间字符串
 */
export function formatDraftTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    
    // 计算时间差（分钟）
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diffMinutes < 1) {
      return '刚刚';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`;
    } else if (diffMinutes < 1440) {
      const hours = Math.floor(diffMinutes / 60);
      return `${hours}小时前`;
    } else {
      const days = Math.floor(diffMinutes / 1440);
      return `${days}天前`;
    }
  } catch (error) {
    return '未知时间';
  }
}
