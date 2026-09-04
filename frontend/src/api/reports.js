import client from './client'

export async function generateReport(patientId) {
  const { data } = await client.post(`/api/v1/reports/${patientId}/generate`)
  return data
}

export async function listReports(patientId) {
  const { data } = await client.get(`/api/v1/reports/${patientId}`)
  return data
}

// Generates the report and immediately downloads the PDF
export async function generateAndDownloadReport(patientId) {
  // 1. Generate the report and get its ID
  const response = await client.post(`/api/v1/reports/${patientId}/generate`)
  const reportId = response.data.id

  // 2. Fetch the generated PDF
  const pdfResponse = await client.get(
    `/api/v1/reports/${patientId}/${reportId}/pdf`,
    {
      responseType: 'blob'
    }
  )

  // 3. Trigger the browser download
  const url = window.URL.createObjectURL(
    new Blob([pdfResponse.data], { type: 'application/pdf' })
  )

  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'DIAZO_Health_Report.pdf')

  document.body.appendChild(link)
  link.click()
  link.parentNode.removeChild(link)

  // Clean up the temporary object URL
  window.URL.revokeObjectURL(url)

  return response.data
}