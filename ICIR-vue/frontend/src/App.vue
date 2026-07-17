<script setup lang="ts">
const marqueeItems = Array.from({ length: 12 }, (_, index) => index)
</script>

<template>
  <div class="marquee" aria-hidden="true">
    <div class="line">
      <span v-for="item in marqueeItems" :key="item" class="mitem">
        <img class="logo" src="/marquee-logo.svg" alt="" />
        T R E A D L E&nbsp;&nbsp; F O U N T A I N
      </span>
    </div>
  </div>
  <router-view />
</template>
