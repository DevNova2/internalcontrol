<template>
  <article class="panel">
    <div class="panel-header">
      <h2 class="panel-title">{{ title }}</h2>
      <span v-if="tag" class="panel-tag">{{ tag }}</span>
    </div>
    <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
    <slot />
  </article>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  tag: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>
