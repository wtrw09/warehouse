// 常用单位列表常量
export const COMMON_UNITS = [
  '个',
  '套',
  '桶',
  '件',
  '只',
  '把',
  '条',
  '米',
  '公斤',
  '升',
  '箱',
  '包',
  '卷',
  '瓶',
  '袋',
  '对',
  '副',
  '双',
  '根',
  '块',
  '本',
  '页'
] as const;

// 单位类型定义
export type CommonUnit = typeof COMMON_UNITS[number];