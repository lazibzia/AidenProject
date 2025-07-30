"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { mockScrapingSources } from "@/lib/mock-data"
import type { ScrapingSource } from "@/lib/types"
import { Search, ChevronLeft, ChevronRight, CheckCircle, XCircle, Clock } from "lucide-react"

const ITEMS_PER_PAGE = 5

export default function DataSourcesPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [currentPage, setCurrentPage] = useState(1)

  const filteredSources = useMemo(() => {
    return mockScrapingSources.filter(
      (source) =>
        source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        source.endpoint.toLowerCase().includes(searchTerm.toLowerCase()),
    )
  }, [searchTerm])

  const totalPages = Math.ceil(filteredSources.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const endIndex = startIndex + ITEMS_PER_PAGE
  const currentSources = filteredSources.slice(startIndex, endIndex)

  const handlePreviousPage = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1))
  }

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
  }

  const getStatusBadgeVariant = (status: ScrapingSource["status"]) => {
    switch (status) {
      case "active":
        return "default"
      case "inactive":
        return "secondary"
      case "error":
        return "destructive"
      default:
        return "outline"
    }
  }

  const getStatusIcon = (status: ScrapingSource["status"]) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "inactive":
        return <Clock className="h-4 w-4 text-yellow-600" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return null
    }
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Data Sources</h1>
        <p className="text-gray-600">Manage and monitor external data scraping sources</p>
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search data sources..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setCurrentPage(1) // Reset to first page on search
              }}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Data Sources Table */}
      <Card>
        <CardHeader>
          <CardTitle>Scraping Websites</CardTitle>
          <CardDescription>
            Showing {currentSources.length} of {filteredSources.length} data sources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Source Name</th>
                  <th className="text-left p-3">Endpoint</th>
                  <th className="text-left p-3">Last Ingestion</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Records Today</th>
                  <th className="text-left p-3">Frequency</th>
                </tr>
              </thead>
              <tbody>
                {currentSources.length > 0 ? (
                  currentSources.map((source) => (
                    <tr key={source.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <p className="font-medium text-sm">{source.name}</p>
                      </td>
                      <td className="p-3">
                        <p className="text-sm text-gray-600 truncate max-w-xs">{source.endpoint}</p>
                      </td>
                      <td className="p-3">
                        <p className="text-sm">{source.last_ingestion}</p>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(source.status)}
                          <Badge variant={getStatusBadgeVariant(source.status)}>{source.status.toUpperCase()}</Badge>
                        </div>
                      </td>
                      <td className="p-3">
                        <p className="font-medium text-sm">{source.records_today}</p>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="capitalize">
                          {source.frequency}
                        </Badge>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-gray-500">
                      No data sources found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {filteredSources.length > ITEMS_PER_PAGE && (
            <div className="flex justify-between items-center mt-4">
              <Button
                variant="outline"
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                className="bg-transparent"
              >
                <ChevronLeft className="h-4 w-4 mr-2" /> Previous
              </Button>
              <span className="text-sm text-gray-700">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="bg-transparent"
              >
                Next <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
