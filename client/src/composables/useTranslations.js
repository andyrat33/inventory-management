import { useI18n } from './useI18n'

// Shared raw-string -> i18n-key maps for the small enum-like values that show up
// in table cells across several views. These were previously hand-rolled (and
// re-allocated on every call) in Dashboard/Spending/Inventory/Restocking.
//
// Each map is plain data (module-level, built once). The returned helpers call
// t() lazily per lookup, so they stay reactive to the active locale without
// rebuilding a lookup object on every invocation.

// Product categories (raw values from inventory/order data)
const CATEGORY_KEYS = {
  'Circuit Boards': 'categories.circuitBoards',
  Sensors: 'categories.sensors',
  Actuators: 'categories.actuators',
  Controllers: 'categories.controllers',
  'Power Supplies': 'categories.powerSupplies',
  // Spending categories (Spending.vue also routes spending-category raw values
  // through its translateCategory). Raw strings don't collide with the product
  // categories above, so a single map preserves the previous behaviour.
  'Raw Materials': 'spendingCategories.rawMaterials',
  Components: 'spendingCategories.components',
  Equipment: 'spendingCategories.equipment',
  Consumables: 'spendingCategories.consumables'
}

const MONTH_KEYS = {
  Jan: 'months.jan',
  Feb: 'months.feb',
  Mar: 'months.mar',
  Apr: 'months.apr',
  May: 'months.may',
  Jun: 'months.jun',
  Jul: 'months.jul',
  Aug: 'months.aug',
  Sep: 'months.sep',
  Oct: 'months.oct',
  Nov: 'months.nov',
  Dec: 'months.dec'
}

const STOCK_LEVEL_KEYS = {
  'In Stock': 'status.inStock',
  'Low Stock': 'status.lowStock'
}

const PRIORITY_KEYS = {
  high: 'priority.high',
  medium: 'priority.medium',
  low: 'priority.low',
  High: 'priority.high',
  Medium: 'priority.medium',
  Low: 'priority.low'
}

export function useTranslations() {
  const { t } = useI18n()

  const lookup = (map, raw) => {
    const key = map[raw]
    return key ? t(key) : raw
  }

  return {
    translateCategory: (raw) => lookup(CATEGORY_KEYS, raw),
    translateMonth: (raw) => lookup(MONTH_KEYS, raw),
    translateStockLevel: (raw) => lookup(STOCK_LEVEL_KEYS, raw),
    translatePriority: (raw) => lookup(PRIORITY_KEYS, raw)
  }
}
