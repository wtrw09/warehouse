<template>
  <div class="svg-icon" v-html="svgContent"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  width: {
    type: String,
    default: '24px'
  },
  height: {
    type: String,
    default: '24px'
  }
})

const svgContent = ref('')

// 加载SVG文件
const loadSvg = async (src) => {
  try {
    // 检查src是否为undefined或空
    if (!src) {
      console.warn('SVG src is undefined or empty');
      return;
    }
    
    // 如果是相对路径（以assets开头），使用Vite的import方式
    if (src.startsWith('/assets/') || src.startsWith('assets/')) {
      try {
        // 使用Vite的动态导入功能
        const module = await import(/* @vite-ignore */ src);
        if (module.default) {
          // 如果是ES模块，获取默认导出
          const response = await fetch(module.default);
          if (response.ok) {
            const svgText = await response.text();
            svgContent.value = svgText;
            return;
          }
        }
      } catch (importError) {
        console.warn('SVG import failed, falling back to fetch:', importError);
      }
    }
    
    // 对于其他情况，使用fetch加载
    const response = await fetch(src);
    if (response.ok) {
      const svgText = await response.text();
      svgContent.value = svgText;
    } else {
      console.error('Failed to fetch SVG:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('Failed to load SVG:', error);
  }
}

onMounted(() => {
  loadSvg(props.src);
})

// 监听src变化
watch(() => props.src, (newSrc) => {
  loadSvg(newSrc);
})
</script>

<style scoped>
.svg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.svg-icon :deep(svg) {
  width: v-bind(width);
  height: v-bind(height);
  fill: currentColor;
}
</style>