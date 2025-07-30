export function exportToCsv<T extends Record<string, any>>(data: T[], filename: string) {
  if (!data || data.length === 0) {
    console.warn("No data to export.")
    return
  }

  // Get headers from the first object's keys
  const headers = Object.keys(data[0])
  const csvRows = []

  // Add header row
  csvRows.push(headers.map((header) => `"${header}"`).join(","))

  // Add data rows
  for (const row of data) {
    const values = headers.map((header) => {
      const value = row[header]
      // Handle null/undefined, escape double quotes, and wrap in quotes
      return `"${value === null || value === undefined ? "" : String(value).replace(/"/g, '""')}"`
    })
    csvRows.push(values.join(","))
  }

  const csvString = csvRows.join("\n")
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")

  if (link.download !== undefined) {
    // Browsers that support HTML5 download attribute
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", filename)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url) // Clean up the URL object
  } else {
    // Fallback for older browsers
    alert("Your browser does not support downloading files directly. Please save the content manually.")
  }
}
