<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <h1>{{ t('nav.companyName') }}</h1>
        <p class="login-subtitle">{{ t('nav.subtitle') }}</p>
      </div>

      <p class="login-demo-note">{{ t('login.demoNote') }}</p>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-field">
          <label for="login-email">{{ t('login.email') }}</label>
          <input id="login-email" v-model="email" type="email" name="email" autocomplete="username" />
        </div>

        <div class="form-field">
          <label for="login-password">{{ t('login.password') }}</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            name="password"
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="login-btn" :disabled="!canSubmit">
          {{ t('login.signIn') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Login',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { login } = useAuth()
    const { t } = useI18n()

    const email = ref('')
    const password = ref('')

    const canSubmit = computed(() => email.value.trim() !== '' && password.value.trim() !== '')

    const handleSubmit = () => {
      if (!canSubmit.value) return
      // Demo-only: no network request, just flips the shared auth flag.
      login()
      const redirect = route.query.redirect
      router.push(typeof redirect === 'string' ? redirect : '/')
    }

    return {
      t,
      email,
      password,
      canSubmit,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1.5rem;
  background: #f8fafc;
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
}

.login-brand {
  text-align: center;
  margin-bottom: 1.25rem;
}

.login-brand h1 {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.login-subtitle {
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
}

.login-demo-note {
  margin-bottom: 1.5rem;
  padding: 0.625rem 0.75rem;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 0.813rem;
  color: #64748b;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.form-field input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: inherit;
}

.form-field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.login-btn {
  margin-top: 0.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.login-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.login-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
