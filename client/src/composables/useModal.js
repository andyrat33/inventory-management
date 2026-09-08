import { watch, nextTick, onUnmounted } from 'vue'

// Shared accessibility behaviour for modal dialogs:
// - Escape closes the modal
// - focus moves into the dialog on open and returns to the previously-focused
//   element on close
// - Tab / Shift+Tab are trapped within the dialog
// Listeners are attached only while the modal is open and always cleaned up.
//
// Usage (inside setup / <script setup>):
//   const dialogRef = ref(null)
//   useModal(() => props.isOpen, close, dialogRef)
// and bind ref="dialogRef" (plus tabindex="-1") to the dialog container.

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(', ')

export function useModal(isOpen, onClose, dialogRef) {
  let previouslyFocused = null

  const getFocusable = () => {
    const root = dialogRef.value
    if (!root) return []
    return Array.from(root.querySelectorAll(FOCUSABLE_SELECTOR)).filter(
      (el) => el.offsetParent !== null || el === document.activeElement
    )
  }

  const handleKeydown = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      onClose()
      return
    }

    if (event.key !== 'Tab') return

    const focusable = getFocusable()
    const root = dialogRef.value
    if (!root) return

    if (focusable.length === 0) {
      event.preventDefault()
      root.focus()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const active = document.activeElement

    if (event.shiftKey) {
      if (active === first || !root.contains(active)) {
        event.preventDefault()
        last.focus()
      }
    } else if (active === last || !root.contains(active)) {
      event.preventDefault()
      first.focus()
    }
  }

  const activate = async () => {
    previouslyFocused = document.activeElement
    document.addEventListener('keydown', handleKeydown, true)
    await nextTick()
    const focusable = getFocusable()
    if (focusable.length > 0) {
      focusable[0].focus()
    } else {
      dialogRef.value?.focus()
    }
  }

  const deactivate = () => {
    document.removeEventListener('keydown', handleKeydown, true)
    if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
      previouslyFocused.focus()
    }
    previouslyFocused = null
  }

  watch(isOpen, (open) => {
    if (open) {
      activate()
    } else {
      deactivate()
    }
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown, true)
  })
}
