const isBlank = (v) => v === null || v === undefined || v === ''

export function sortRows (rows, key, dir = 'asc') {
  const copy = [...rows]
  if (!key) return copy
  const sign = dir === 'desc' ? -1 : 1
  return copy.sort((a, b) => {
    const x = a[key]
    const y = b[key]
    if (isBlank(x) && isBlank(y)) return 0
    if (isBlank(x)) return 1
    if (isBlank(y)) return -1
    if (typeof x === 'number' && typeof y === 'number') return (x - y) * sign
    return String(x).localeCompare(String(y), undefined, { sensitivity: 'base', numeric: true }) * sign
  })
}
