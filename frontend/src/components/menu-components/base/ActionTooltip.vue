<template>
  <el-tooltip 
    :content="content" 
    :placement="placement" 
    :disabled="disabled"
    class="base-tooltip-trigger"
  >
    <slot />
  </el-tooltip>
</template>

<script setup lang="ts">
interface Props {
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  placement: 'top',
  disabled: false
})
</script>

<style scoped>
/* 导入基础样式 */
@import '../../../css/base-styles.css';
</style>