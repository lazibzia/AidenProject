import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div>
                <Skeleton className="h-6 w-48 mb-1" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Badge variant="secondary">LOADING</Badge>
            </div>
            <Skeleton className="h-10 w-24" />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Limited Access Notice Skeleton */}
          <div className="mb-6">
            <div className="bg-blue-50 border-blue-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Skeleton className="h-5 w-5 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-4 w-3/4 mb-1" />
                  <Skeleton className="h-4 w-full" />
                </div>
              </div>
            </div>
          </div>

          {/* User Profile Card Skeleton */}
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center space-x-4">
                <Skeleton className="w-16 h-16 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-6 w-48 mb-1" />
                  <Skeleton className="h-4 w-32 mb-2" />
                  <div className="flex space-x-2">
                    <Badge variant="secondary">Loading</Badge>
                    <Badge variant="outline">Loading</Badge>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Limited Stats Overview Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Skeleton className="h-8 w-8 rounded-full" />
                  <div className="ml-4">
                    <Skeleton className="h-4 w-24 mb-1" />
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-3 w-20 mt-1" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Available Actions Skeleton */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <Skeleton className="h-6 w-48 mb-4" />
                <div className="space-y-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Client Activity Skeleton */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <Skeleton className="h-6 w-48 mb-4" />
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <Skeleton className="w-8 h-8 rounded-full" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-3/4 mb-1" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="h-8 w-16" />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Restricted Areas Notice Skeleton */}
            <div className="lg:col-span-2 bg-red-50 border-red-200 rounded-lg shadow">
              <div className="p-6">
                <Skeleton className="h-6 w-64 mb-4" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-40 mb-2" />
                    <div className="space-y-1">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-40 mb-2" />
                    <div className="space-y-1">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                    </div>
                  </div>
                </div>
                <Skeleton className="h-16 w-full mt-4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
