"use client";

import { useState, useMemo, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Download,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import Link from "next/link";
import axiospermit from "@/lib/permitaxios";
import { saveAs } from "file-saver";

interface Permit {
  city: string;
  permit_num: string;
  permit_type: string;
  description: string;
  applied_date: string;
  issued_date: string;
  current_status: string;
  applicant_name: string;
  applicant_address: string;
  contractor_name: string;
  contractor_address: string;
}

interface ApiResponse {
  permits: Permit[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

const DEFAULT_LIMIT = 10;

export default function PermitsPage() {
  const [apiData, setApiData] = useState<ApiResponse>({
    permits: [],
    total: 0,
    page: 1,
    limit: DEFAULT_LIMIT,
    pages: 1,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [dateRange, setDateRange] = useState("daily");
  const [startDate, setStartDate] = useState(() => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    return yesterday.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [minValuation, setMinValuation] = useState("");
  const [maxValuation, setMaxValuation] = useState("");
  const [schedulerHour, setSchedulerHour] = useState("00");
  const [schedulerMinute, setSchedulerMinute] = useState("00");
  const [cityFilter, setCityFilter] = useState("");
  const [scrapeCity, setScrapeCity] = useState("austin");
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const fetchPermits = async (
    page: number = 1,
    limit: number = DEFAULT_LIMIT
  ) => {
    try {
      setIsLoading(true);
      const response = await axiospermit.get("/api/permits", {
        params: {
          page,
          limit,
          search: searchTerm,
          city: cityFilter,
          start_date: startDate,
          end_date: endDate,
        },
      });
      setApiData(response.data);
    } catch (error) {
      console.error("Error fetching permits:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPermits();
  }, [searchTerm, cityFilter, startDate, endDate]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= apiData.pages) {
      fetchPermits(newPage);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await axiospermit.get("/api/permits/export", {
        params: {
          search: searchTerm,
          city: cityFilter,
          start_date: startDate,
          end_date: endDate,
        },
        responseType: "blob", // Important for file downloads
      });

      // Create a blob from the response data
      const blob = new Blob([response.data], { type: "text/csv" });

      // Create a filename with the current date
      const today = new Date();
      const dateString = today.toISOString().split("T")[0];
      const filename = `permits_export_${dateString}.csv`;

      // Use file-saver to save the file
      saveAs(blob, filename);
    } catch (error) {
      console.error("Error exporting data:", error);
      alert("Failed to export data. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  const updateScheduler = () => {
    console.log(`Scheduler set to run at ${schedulerHour}:${schedulerMinute}`);
  };

  const runScrape = async () => {
    try {
      setIsLoading(true);
      const response = await axiospermit.post("/api/scrape", null, {
        params: {
          city: scrapeCity,
          mode: dateRange,
          start_date: startDate,
          end_date: endDate,
        },
      });

      // Refresh permits after scrape
      await fetchPermits(apiData.page);

      alert(response.data.message || "Scrape completed.");
    } catch (error: any) {
      alert(
        "Scrape failed: " + (error?.response?.data?.message || error.message)
      );
    } finally {
      setIsLoading(false);
    }
  };

  const renderPaginationControls = () => {
    const maxVisiblePages = 5;
    const halfVisible = Math.floor(maxVisiblePages / 2);
    let startPage = Math.max(1, apiData.page - halfVisible);
    let endPage = Math.min(apiData.pages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    return (
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(1)}
          disabled={apiData.page === 1 || isLoading}
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(apiData.page - 1)}
          disabled={apiData.page === 1 || isLoading}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        {startPage > 1 && (
          <Button variant="ghost" size="sm" disabled>
            ...
          </Button>
        )}

        {Array.from(
          { length: endPage - startPage + 1 },
          (_, i) => startPage + i
        ).map((page) => (
          <Button
            key={page}
            variant={page === apiData.page ? "default" : "outline"}
            size="sm"
            onClick={() => handlePageChange(page)}
            disabled={isLoading}
          >
            {page}
          </Button>
        ))}

        {endPage < apiData.pages && (
          <Button variant="ghost" size="sm" disabled>
            ...
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(apiData.page + 1)}
          disabled={apiData.page === apiData.pages || isLoading}
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(apiData.pages)}
          disabled={apiData.page === apiData.pages || isLoading}
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Permits Database</h1>
        <p className="text-gray-600">Residential Permits Dashboard</p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Scrape Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Scrape City
              </label>
              <Input
                type="text"
                value={scrapeCity}
                onChange={(e) => setScrapeCity(e.target.value)}
                placeholder="e.g., austin"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Scrape Mode
              </label>
              <Select
                value={dateRange}
                onValueChange={(value) => {
                  setDateRange(value);
                  const today = new Date();
                  const newStartDate = new Date();
                  let newEndDate = new Date();

                  if (value !== "custom") {
                    newEndDate.setTime(today.getTime());
                    switch (value) {
                      case "daily":
                        newStartDate.setDate(today.getDate() - 1);
                        break;
                      case "weekly":
                        newStartDate.setDate(today.getDate() - 7);
                        break;
                      case "monthly":
                        newStartDate.setMonth(today.getMonth() - 1);
                        break;
                    }
                    setStartDate(newStartDate.toISOString().split("T")[0]);
                    setEndDate(newEndDate.toISOString().split("T")[0]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="custom">Custom Range</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {dateRange === "custom" && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Start Date
                  </label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    End Date
                  </label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </>
            )}
            <div className="flex items-end">
              <Button
                className="w-full"
                onClick={runScrape}
                disabled={isLoading}
              >
                {isLoading ? "Scraping..." : "Run Scrape"}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div>
              <label className="block text-sm font-medium mb-1">
                Scheduler Hour
              </label>
              <Select value={schedulerHour} onValueChange={setSchedulerHour}>
                <SelectTrigger>
                  <SelectValue placeholder="00" />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 24 }, (_, i) =>
                    i.toString().padStart(2, "0")
                  ).map((hour) => (
                    <SelectItem key={hour} value={hour}>
                      {hour}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Scheduler Minute
              </label>
              <Select
                value={schedulerMinute}
                onValueChange={setSchedulerMinute}
              >
                <SelectTrigger>
                  <SelectValue placeholder="00" />
                </SelectTrigger>
                <SelectContent>
                  {["00", "15", "30", "45"].map((minute) => (
                    <SelectItem key={minute} value={minute}>
                      {minute}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end col-span-2 md:col-span-1">
              <Button className="w-full" onClick={updateScheduler}>
                Update Scheduler
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-6">
            <div>
              <label className="block text-sm font-medium mb-1">
                Search (Permit #, Contractor, or Description)
              </label>
              <Input
                type="text"
                placeholder="Search permits..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    fetchPermits();
                  }
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">City</label>
              <Input
                type="text"
                placeholder="Filter by city"
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    fetchPermits();
                  }
                }}
              />
            </div>

            <div className="flex items-end space-x-2">
              <Button className="w-full" onClick={() => fetchPermits()}>
                Apply Filters <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
              <Button onClick={handleExport} disabled={isExporting}>
                <Download className="h-4 w-4 mr-2" />
                {isExporting ? "Exporting..." : "Export CSV"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Permits</CardTitle>
          <p className="text-sm text-gray-600">
            Showing {apiData.permits.length} of {apiData.total} permits (
            {formatDate(startDate)} to {formatDate(endDate)})
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border rounded-lg">
              <thead className="bg-gray-100 text-xs font-medium uppercase">
                <tr className="border-b">
                  <th className="text-left p-3">Permit #</th>
                  <th className="text-left p-3">Type</th>
                  <th className="text-left p-3">Description</th>
                  <th className="text-left p-3">Contractor</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Applied</th>
                  <th className="text-left p-3">Issued</th>
                  <th className="text-left p-3">City</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="h-24 text-center text-gray-500">
                      Loading permits...
                    </td>
                  </tr>
                ) : apiData.permits.length > 0 ? (
                  apiData.permits.map((permit, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <Link
                          href={`/permits/${permit.permit_num}`}
                          className="text-blue-600 hover:underline"
                        >
                          {permit.permit_num}
                        </Link>
                      </td>
                      <td className="p-3">{permit.permit_type}</td>
                      <td className="p-3">{permit.description}</td>
                      <td className="p-3">{permit.contractor_name || "N/A"}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            permit.current_status === "Active"
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {permit.current_status}
                        </span>
                      </td>
                      <td className="p-3">{formatDate(permit.applied_date)}</td>
                      <td className="p-3">{formatDate(permit.issued_date)}</td>
                      <td className="p-3">{permit.city}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="h-24 text-center text-gray-500">
                      No permits found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center mt-4 gap-4">
            <div className="text-sm text-gray-600">
              Showing {apiData.permits.length} of {apiData.total} items (Page{" "}
              {apiData.page} of {apiData.pages})
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm">Rows per page:</span>
                <Select
                  value={apiData.limit.toString()}
                  onValueChange={(value) => {
                    fetchPermits(1, Number(value));
                  }}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[10, 20, 50, 100].map((size) => (
                      <SelectItem key={size} value={size.toString()}>
                        {size}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {renderPaginationControls()}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
