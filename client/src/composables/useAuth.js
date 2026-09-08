import { ref, computed } from 'vue'
import { useI18n } from './useI18n'

// Base user data (language-independent)
const baseUserData = {
  id: 1,
  email: 'john.doe@catalystcomponents.com',
  phone: '+1 (111) 111-1111',
  avatar: null,
  joinDate: '2022-03-15'
}

// Mock current user data with language-aware fields
const createCurrentUser = () => {
  const { currentLocale } = useI18n()

  return computed(() => {
    const isJapanese = currentLocale.value === 'ja'

    return {
      ...baseUserData,
      name: isJapanese ? '田中 太郎' : 'John Doe',
      jobTitle: isJapanese ? 'オペレーションマネージャー' : 'Operations Manager',
      department: isJapanese ? 'サプライチェーン運営部' : 'Supply Chain Operations',
      location: isJapanese ? 'サンフランシスコ' : 'San Francisco',
      tasks: isJapanese
        ? [
            {
              id: 1,
              title: '第4四半期の在庫レベルを確認',
              priority: 'high',
              dueDate: '2025-10-08',
              status: 'pending'
            },
            {
              id: 2,
              title: '東京倉庫の注文を承認',
              priority: 'medium',
              dueDate: '2025-10-06',
              status: 'pending'
            },
            {
              id: 3,
              title: '回路基板の再注文点を更新',
              priority: 'medium',
              dueDate: '2025-10-10',
              status: 'pending'
            },
            {
              id: 4,
              title: '月次支出レポートを確認',
              priority: 'low',
              dueDate: '2025-10-15',
              status: 'pending'
            }
          ]
        : [
            {
              id: 1,
              title: 'Review Q4 inventory levels',
              priority: 'high',
              dueDate: '2025-10-08',
              status: 'pending'
            },
            {
              id: 2,
              title: 'Approve Tokyo warehouse orders',
              priority: 'medium',
              dueDate: '2025-10-06',
              status: 'pending'
            },
            {
              id: 3,
              title: 'Update reorder points for Circuit Boards',
              priority: 'medium',
              dueDate: '2025-10-10',
              status: 'pending'
            },
            {
              id: 4,
              title: 'Review monthly spending report',
              priority: 'low',
              dueDate: '2025-10-15',
              status: 'pending'
            }
          ]
    }
  })
}

const currentUser = createCurrentUser()

// Demo-only auth: there is no backend auth (see README "Authentication").
// This just gates the UI behind a token-shaped flag persisted for the tab so a
// reload keeps you signed in and "Log out" genuinely returns you to /login.
const AUTH_KEY = 'demo-auth'

const readAuth = () => {
  try {
    return sessionStorage.getItem(AUTH_KEY) === 'true'
  } catch {
    return false
  }
}

// Module-level so every useAuth() call shares one reactive source of truth.
const isAuthenticated = ref(readAuth())

export function useAuth() {
  const login = () => {
    isAuthenticated.value = true
    try {
      sessionStorage.setItem(AUTH_KEY, 'true')
    } catch {
      /* private mode / storage disabled — flag still lives in memory */
    }
  }

  const logout = () => {
    isAuthenticated.value = false
    try {
      sessionStorage.removeItem(AUTH_KEY)
    } catch {
      /* ignore */
    }
  }

  const getInitials = (name) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
  }

  return {
    currentUser,
    isAuthenticated,
    login,
    logout,
    getInitials
  }
}
