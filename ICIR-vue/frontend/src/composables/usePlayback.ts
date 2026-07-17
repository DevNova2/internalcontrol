import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { HaochiDataset } from '@/lib/chart'

const speedChoices = [30, 60, 120]

interface PlaybackOptions {
  loop?: boolean
  loopDelayMs?: number
}

export function usePlayback(dataset: () => HaochiDataset | null, options: PlaybackOptions = {}) {
  const currentIndex = ref(0)
  const isPlaying = ref(false)
  const speedMs = ref(60)
  let timer: ReturnType<typeof setInterval> | null = null
  let restartTimer: ReturnType<typeof setTimeout> | null = null

  const maxIndex = computed(() => {
    const source = dataset()
    return source ? Math.max(0, source.dates.length - 1) : 0
  })

  const currentDate = computed(() => {
    const source = dataset()
    return source?.dates[currentIndex.value] ?? '--'
  })

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    if (restartTimer) {
      clearTimeout(restartTimer)
      restartTimer = null
    }
    isPlaying.value = false
  }

  function tick() {
    if (maxIndex.value === 0) {
      currentIndex.value = 0
      return
    }
    if (currentIndex.value >= maxIndex.value) {
      if (options.loop) {
        if (timer) {
          clearInterval(timer)
          timer = null
        }
        restartTimer = setTimeout(() => {
          restartTimer = null
          currentIndex.value = 0
          play()
        }, options.loopDelayMs ?? 0)
        return
      }
      stop()
      return
    }
    currentIndex.value += 1
  }

  function play() {
    if (!dataset()) return
    stop()
    isPlaying.value = true
    timer = setInterval(tick, speedMs.value)
  }

  function pause() {
    stop()
  }

  function reset() {
    stop()
    currentIndex.value = 0
  }

  function jumpToEnd() {
    stop()
    currentIndex.value = maxIndex.value
  }

  watch(speedMs, () => {
    if (isPlaying.value) {
      play()
    }
  })

  watch(maxIndex, (value) => {
    if (currentIndex.value > value) {
      currentIndex.value = value
    }
  })

  onBeforeUnmount(stop)

  return {
    currentDate,
    currentIndex,
    isPlaying,
    jumpToEnd,
    maxIndex,
    pause,
    play,
    reset,
    speedChoices,
    speedMs,
  }
}
