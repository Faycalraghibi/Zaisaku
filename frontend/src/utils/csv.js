// Spreadsheet apps execute cells starting with these characters as formulas.
const FORMULA_START = /^[=+@\t\r]/

const toCell = (value) => {
  if (value === null || value === undefined) return ''
  let text = String(value)
  if (typeof value === 'string' && (FORMULA_START.test(text) || (text.startsWith('-') && Number.isNaN(Number(text))))) {
    text = `'${text}`
  }
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

// columns: [{ label, key } | { label, value: (row) => any }]
export function toCsv (columns, rows) {
  const header = columns.map((c) => toCell(c.label)).join(',')
  const body = rows.map((row) => columns.map((c) => toCell(c.value ? c.value(row) : row[c.key])).join(','))
  return `${[header, ...body].join('\r\n')}\r\n`
}

export function downloadCsv (filename, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
