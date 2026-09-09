<template>
  <div class="inventory">
    <div class="page-header">
      <h2>{{ t('inventory.title') }}</h2>
      <p>{{ t('inventory.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('inventory.stockLevels') }} ({{ filteredItems.length }} {{ t('inventory.skus') }})
          </h3>
          <div class="header-actions">
            <div class="search-box">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                  clip-rule="evenodd"
                />
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="t('inventory.searchPlaceholder')"
                class="search-input"
              />
              <button
                v-if="searchQuery"
                @click="searchQuery = ''"
                class="clear-search"
                :title="t('inventory.clearSearch')"
                :aria-label="t('inventory.clearSearch')"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clip-rule="evenodd"
                  />
                </svg>
              </button>
            </div>
            <button
              class="export-csv-btn"
              :disabled="filteredItems.length === 0"
              :aria-label="t('inventory.exportCsv')"
              @click="exportToCsv"
            >
              {{ t('inventory.exportCsv') }}
            </button>
          </div>
        </div>
        <div class="table-container" :class="{ 'is-refreshing': refreshing }">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('inventory.table.sku') }}</th>
                <th scope="col">{{ t('inventory.table.itemName') }}</th>
                <th scope="col">{{ t('inventory.table.category') }}</th>
                <th scope="col">{{ t('inventory.table.quantityOnHand') }}</th>
                <th scope="col">{{ t('inventory.table.reorderPoint') }}</th>
                <th scope="col">{{ t('inventory.table.unitCost') }}</th>
                <th scope="col">{{ t('inventory.table.totalValue') }}</th>
                <th scope="col">{{ t('inventory.table.location') }}</th>
                <th scope="col">{{ t('inventory.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredItems"
                :key="item.id"
                class="clickable-row"
                tabindex="0"
                role="button"
                :aria-label="t('inventory.viewItemDetail', { name: translateProductName(item.name) })"
                @click="showItemDetail(item)"
                @keydown.enter="showItemDetail(item)"
                @keydown.space.prevent="showItemDetail(item)"
              >
                <td>
                  <strong>{{ item.sku }}</strong>
                </td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>
                  <strong>{{ item.quantity_on_hand }}</strong>
                </td>
                <td>{{ item.reorder_point }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td>
                  <strong
                    >{{ currencySymbol
                    }}{{
                      (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })
                    }}</strong
                  >
                </td>
                <td>{{ translateWarehouse(item.location) }}</td>
                <td>
                  <span :class="['badge', getStockStatusClass(item)]">
                    {{ getStockStatus(item) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <InventoryDetailModal :is-open="showItemModal" :inventory-item="selectedItem" @close="showItemModal = false" />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { useTranslations } from '../composables/useTranslations'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'

export default {
  name: 'Inventory',
  components: {
    InventoryDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const { translateCategory } = useTranslations()
    const route = useRoute()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    // Separate flag for background refetches (filter changes) so the table
    // keeps showing the previous rows instead of blanking to a spinner.
    const refreshing = ref(false)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Stock status order for sorting (using status keys)
    const STATUS_ORDER = { lowStock: 0, adequate: 1, inStock: 2 }

    // Get stock status key (for sorting and translation)
    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter((item) => item.name.toLowerCase().includes(query))
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    const loadInventory = async ({ initial = false } = {}) => {
      try {
        if (initial) {
          loading.value = true
        } else {
          refreshing.value = true
        }
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
        // Open the detail modal if we were deep-linked to a specific SKU
        openFromQuery()
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
        refreshing.value = false
      }
    }

    // If ?item=<sku> is present, open that item's detail modal (no-op if not found)
    const openFromQuery = () => {
      const sku = route.query.item
      if (!sku) return
      const match = items.value.find((it) => it.sku === sku)
      if (match) showItemDetail(match)
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    // React to deep-link changes without a full reload when data is already loaded
    watch(() => route.query.item, openFromQuery)

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'danger'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'warning'
      } else {
        return 'success'
      }
    }

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    // Plain English status labels for CSV export (locale-independent, not via t())
    const CSV_STATUS_LABELS = {
      lowStock: 'Low Stock',
      adequate: 'Adequate',
      inStock: 'In Stock'
    }

    // Escape a single CSV field: wrap in double quotes when it contains a
    // comma, double-quote or newline, and double up any internal quotes.
    const escapeCsvField = (value) => {
      let str = String(value ?? '')
      // Neutralise spreadsheet formula injection: a leading =, +, -, @, tab or CR
      // makes Excel/Sheets evaluate the cell as a formula, so prefix an apostrophe.
      if (/^[=+\-@\t\r]/.test(str)) {
        str = "'" + str
      }
      if (/[",\n]/.test(str)) {
        return '"' + str.replace(/"/g, '""') + '"'
      }
      return str
    }

    // Build and download a CSV of the currently displayed rows (filteredItems).
    const exportToCsv = () => {
      if (filteredItems.value.length === 0) return

      const headers = [
        'SKU',
        'Item Name',
        'Category',
        'Quantity on Hand',
        'Reorder Point',
        'Unit Cost',
        'Total Value',
        'Location',
        'Status'
      ]

      const rows = filteredItems.value.map((item) => {
        // Use raw data values, not translated/formatted display values
        const totalValue = item.quantity_on_hand * item.unit_cost
        return [
          item.sku,
          item.name,
          item.category,
          item.quantity_on_hand,
          item.reorder_point,
          item.unit_cost.toFixed(2),
          totalValue.toFixed(2),
          item.location,
          CSV_STATUS_LABELS[getStockStatusKey(item)]
        ]
      })

      const csv = [headers, ...rows].map((row) => row.map(escapeCsvField).join(',')).join('\n')

      // Today's date as YYYY-MM-DD for the filename
      const today = new Date()
      const dateStr = [
        today.getFullYear(),
        String(today.getMonth() + 1).padStart(2, '0'),
        String(today.getDate()).padStart(2, '0')
      ].join('-')

      // Trigger download via Blob + temporary anchor, then revoke the object URL
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `inventory-export-${dateStr}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }

    onMounted(() => loadInventory({ initial: true }))

    return {
      t,
      loading,
      refreshing,
      error,
      items,
      searchQuery,
      filteredItems,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      currencySymbol,
      translateProductName,
      translateWarehouse,
      exportToCsv
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 300px;
}

.export-csv-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
  white-space: nowrap;
}

.export-csv-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.export-csv-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  width: 18px;
  height: 18px;
  color: #64748b;
  pointer-events: none;
}

/* Dim (but keep visible) the table while a filter-triggered refetch is in flight */
.table-container.is-refreshing {
  opacity: 0.6;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 2.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #0f172a;
  background: #f8fafc;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #475569;
}

.clear-search {
  position: absolute;
  right: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-search:hover {
  background: #e2e8f0;
  color: #64748b;
}

.clear-search:focus-visible,
.export-csv-btn:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.clear-search svg {
  width: 18px;
  height: 18px;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.error {
  color: #ef4444;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.clickable-row:hover {
  background: #eff6ff !important;
}

.clickable-row:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
}
</style>
