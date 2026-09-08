<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyRows" :key="q.quarter">
                <td>
                  <strong>{{ q.quarter }}</strong>
                </td>
                <td>{{ q.totalOrders }}</td>
                <td>{{ q.totalRevenue }}</td>
                <td>{{ q.avgOrderValue }}</td>
                <td>
                  <span :class="q.fulfillmentClass">{{ q.fulfillmentRate }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="bar in monthlyChartRows" :key="bar.month" class="bar-wrapper">
              <div class="bar-container">
                <div class="bar" :style="{ height: bar.height + 'px' }" :title="bar.title"></div>
              </div>
              <div class="bar-label">{{ bar.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.momAnalysis.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.momAnalysis.month') }}</th>
                <th>{{ t('reports.momAnalysis.orders') }}</th>
                <th>{{ t('reports.momAnalysis.revenue') }}</th>
                <th>{{ t('reports.momAnalysis.change') }}</th>
                <th>{{ t('reports.momAnalysis.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="month in monthlyRows" :key="month.month">
                <td>
                  <strong>{{ month.label }}</strong>
                </td>
                <td>{{ month.orderCount }}</td>
                <td>{{ month.revenue }}</td>
                <td>
                  <span :class="month.changeClass">{{ month.changeText }}</span>
                </td>
                <td>
                  <span :class="month.changeClass">{{ month.growthText }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenueYtd') }}</div>
          <div class="stat-value">{{ summaryStats.totalRevenue }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ summaryStats.avgMonthlyRevenue }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrdersYtd') }}</div>
          <div class="stat-value">{{ summaryStats.totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ summaryStats.bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useI18n } from '../composables/useI18n'

const API_BASE_URL = 'http://localhost:8001/api'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

export default {
  name: 'Reports',
  setup() {
    const { t } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // --- Pure formatting helpers (no I/O, no O(n) scans) ---

    // Format a number as "1,234.56" (grouped integer part, exactly 2 decimals)
    const formatCurrency = (num) => {
      const value = Number(num) || 0
      return (
        '$' +
        value.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })
      )
    }

    // Convert "YYYY-MM" to a localised "Mon YYYY" label
    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-')
      const key = MONTH_KEYS[parseInt(month, 10) - 1]
      const name = key ? t(`months.${key}`) : month
      return `${name} ${year}`
    }

    const fulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const changeClass = (delta) => {
      if (delta > 0) return 'positive-change'
      if (delta < 0) return 'negative-change'
      return ''
    }

    const changeText = (delta) => {
      if (delta > 0) return '+' + formatCurrency(delta)
      if (delta < 0) return '-' + formatCurrency(Math.abs(delta))
      return '$0.00'
    }

    const growthText = (current, previous) => {
      if (previous === 0) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      const sign = rate > 0 ? '+' : ''
      return `${sign}${rate.toFixed(1)}%`
    }

    // --- Derived view-models (computed once per data change, not per render) ---

    const quarterlyRows = computed(() =>
      quarterlyData.value.map((q) => ({
        quarter: q.quarter,
        totalOrders: q.total_orders,
        totalRevenue: formatCurrency(q.total_revenue),
        avgOrderValue: formatCurrency(q.avg_order_value),
        fulfillmentRate: `${q.fulfillment_rate}%`,
        fulfillmentClass: fulfillmentClass(q.fulfillment_rate)
      }))
    )

    // Single O(n) pass for the tallest bar; bar heights then derive in O(1)
    const maxMonthlyRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => (m.revenue > max ? m.revenue : max), 0)
    )

    const monthlyChartRows = computed(() => {
      const max = maxMonthlyRevenue.value
      return monthlyData.value.map((m) => ({
        month: m.month,
        label: formatMonth(m.month),
        height: max === 0 ? 0 : (m.revenue / max) * 200,
        title: formatCurrency(m.revenue)
      }))
    })

    const monthlyRows = computed(() =>
      monthlyData.value.map((m, index) => {
        const prev = index > 0 ? monthlyData.value[index - 1].revenue : null
        const delta = prev === null ? 0 : m.revenue - prev
        return {
          month: m.month,
          label: formatMonth(m.month),
          orderCount: m.order_count,
          revenue: formatCurrency(m.revenue),
          changeText: prev === null ? '-' : changeText(delta),
          growthText: prev === null ? '-' : growthText(m.revenue, prev),
          changeClass: prev === null ? '' : changeClass(delta)
        }
      })
    )

    const summaryStats = computed(() => {
      const totalRevenue = monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
      const totalOrders = monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
      const avgMonthlyRevenue = monthlyData.value.length ? totalRevenue / monthlyData.value.length : 0

      let bestQuarter = ''
      let bestRevenue = 0
      for (const q of quarterlyData.value) {
        if (q.total_revenue > bestRevenue) {
          bestRevenue = q.total_revenue
          bestQuarter = q.quarter
        }
      }

      return {
        totalRevenue: formatCurrency(totalRevenue),
        avgMonthlyRevenue: formatCurrency(avgMonthlyRevenue),
        totalOrders,
        bestQuarter: bestQuarter || '-'
      }
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        const [quarterlyResponse, monthlyResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/reports/quarterly`),
          axios.get(`${API_BASE_URL}/reports/monthly-trends`)
        ])

        quarterlyData.value = quarterlyResponse.data
        monthlyData.value = monthlyResponse.data
      } catch (err) {
        error.value = t('reports.loadError', { message: err.message })
      } finally {
        loading.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      quarterlyRows,
      monthlyChartRows,
      monthlyRows,
      summaryStats
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e2e8f0;
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.reports-table tr:hover {
  background: #f8fafc;
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #2563eb, #3b82f6);
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #3b82f6;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}
</style>
