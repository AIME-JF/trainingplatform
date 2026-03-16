export function formatDateTime(value, fallback = '未设置') {
  if (!value) return fallback
  return String(value).replace('T', ' ').slice(0, 19)
}
