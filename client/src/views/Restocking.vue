<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
      </div>
      <div class="budget-control">
        <input
          type="range"
          min="0"
          max="500000"
          step="5000"
          v-model.number="budget"
          @change="loadRecommendations"
          class="budget-slider"
        />
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t('restocking.recommendedItems') }}
          <span v-if="recommendations.length" class="card-title-count">
            &mdash; {{ t('restocking.itemsSelected', { count: recommendations.length }) }}
          </span>
        </h3>
      </div>

      <div v-if="recommendations.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>

      <template v-else>
        <div class="summary-row">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.remainingBudget') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
        </div>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.quantityOnHand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.recommendedQuantity') }}</th>
                <th>{{ t('restocking.table.recommendedCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.forecasted_demand }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ item.recommended_quantity }}</strong></td>
                <td>{{ currencySymbol }}{{ item.recommended_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div class="order-actions">
        <button
          type="button"
          class="place-order-btn"
          :disabled="recommendations.length === 0 || placingOrder"
          @click="placeOrder"
        >
          {{ placingOrder ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
        <p v-if="orderMessage" class="order-message success">{{ orderMessage }}</p>
        <p v-if="orderErrorMsg" class="order-message error-text">{{ orderErrorMsg }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Restocking recommendations are budget-driven only (no warehouse/category/month filters
    // on this endpoint), so we don't pull in useFilters here.
    const budget = ref(100000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)

    const placingOrder = ref(false)
    const orderMessage = ref(null)
    const orderErrorMsg = ref(null)

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.recommended_cost, 0)
    })

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      placingOrder.value = true
      orderMessage.value = null
      orderErrorMsg.value = null
      try {
        const order = await api.createRestockingOrder(budget.value)
        orderMessage.value = `${t('restocking.orderSuccess')} (${order.order_number})`
        // Recommendations may no longer be valid once an order consumes the budget, so refresh them.
        await loadRecommendations()
      } catch (err) {
        orderErrorMsg.value = t('restocking.orderError')
        console.error(err)
      } finally {
        placingOrder.value = false
      }
    }

    // Mirrors Inventory.vue's category translation map (no shared composable for this yet).
    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      recommendations,
      loading,
      error,
      placingOrder,
      orderMessage,
      orderErrorMsg,
      totalCost,
      remainingBudget,
      loadRecommendations,
      placeOrder,
      translateCategory,
      currencySymbol,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.card-title-count {
  font-weight: 500;
  color: #64748b;
  font-size: 0.938rem;
}

.budget-control {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
}

.budget-value {
  min-width: 110px;
  text-align: right;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
}

.order-actions {
  margin-top: 1.25rem;
  padding-top: 1.125rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
}

.place-order-btn {
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

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-message {
  font-size: 0.875rem;
  font-weight: 500;
}

.order-message.success {
  color: #059669;
}

.order-message.error-text {
  color: #dc2626;
}
</style>
