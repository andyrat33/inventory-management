<template>
  <div class="language-switcher">
    <button
      ref="triggerRef"
      class="language-button"
      :class="{ collapsed }"
      :data-tooltip="localeName"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen"
      @click="toggleDropdown"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="globe-icon" aria-hidden="true">
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5" />
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5" />
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5" />
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5" />
      </svg>
      <span v-if="!collapsed" class="language-label">{{ localeName }}</span>
      <svg
        v-if="!collapsed"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </button>

    <div v-if="isDropdownOpen" ref="menuRef" class="dropdown-menu" role="menu" @keydown.esc.prevent="closeDropdown()">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        role="menuitem"
        :class="{ active: currentLocale === locale }"
        @click="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
          aria-hidden="true"
        >
          <path
            d="M4 9L7.5 12.5L14 6"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue'
import { useI18n } from '../composables/useI18n'

defineProps({
  collapsed: { type: Boolean, default: false }
})

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)
const triggerRef = ref(null)
const menuRef = ref(null)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

// Close the menu when a click/tap lands outside both the menu and its trigger
const handleOutsideClick = (event) => {
  if (
    menuRef.value &&
    !menuRef.value.contains(event.target) &&
    triggerRef.value &&
    !triggerRef.value.contains(event.target)
  ) {
    closeDropdown()
  }
}

const openDropdown = async () => {
  isDropdownOpen.value = true
  document.addEventListener('mousedown', handleOutsideClick)
  await nextTick()
  menuRef.value?.querySelector('.dropdown-item')?.focus()
}

const closeDropdown = ({ returnFocus = true } = {}) => {
  if (!isDropdownOpen.value) return
  isDropdownOpen.value = false
  document.removeEventListener('mousedown', handleOutsideClick)
  if (returnFocus) triggerRef.value?.focus()
}

const toggleDropdown = () => {
  if (isDropdownOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

const selectLanguage = (locale) => {
  setLocale(locale)
  closeDropdown()
}

onUnmounted(() => {
  document.removeEventListener('mousedown', handleOutsideClick)
})
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
}

.language-button:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.language-button:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.language-button.collapsed {
  justify-content: center;
  padding: 0.5rem;
  gap: 0;
}

.globe-icon {
  color: #64748b;
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
}

.chevron {
  color: #64748b;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 0;
  min-width: 160px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
  background: #f8fafc;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.language-name {
  flex: 1;
}

.check-icon {
  color: #2563eb;
  flex-shrink: 0;
}
</style>
