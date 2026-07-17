<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="chart-card">
    <div v-if="title" class="chart-card__header">
      <div>
        <h2>{{ title }}</h2>
      </div>
    </div>

    <div class="chart-card__body">
      <slot />
    </div>
  </section>
</template>
