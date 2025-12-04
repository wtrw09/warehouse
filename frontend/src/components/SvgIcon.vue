<template>
  <div class="svg-icon" v-html="svgContent"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

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

onMounted(async () => {
  try {
    const response = await fetch(props.src)
    if (response.ok) {
      const svgText = await response.text()
      svgContent.value = svgText
    }
  } catch (error) {
    console.error('Failed to load SVG:', error)
  }
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