import { useUserStore } from '../stores/user';

/**
 * 权限检查组合式函数
 * 用于检查用户是否具有特定权限
 */
export function usePermission() {
  const userStore = useUserStore();

  /**
   * 检查用户是否具有指定权限
   * @param permissionCode 权限代码
   * @returns 是否具有权限
   */
  const hasPermission = (permissionCode: string) => {
    if (!userStore.userInfo?.permissions) {
      return false;
    }
    // console.log("存储用于权限信息",userStore.userInfo.permissions);
    return userStore.userInfo.permissions.includes(permissionCode);
  };

  return {
    hasPermission
  };
}