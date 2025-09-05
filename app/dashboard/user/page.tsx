import { requireRole } from "@/lib/auth"
import { logoutAction } from "@/lib/actions"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, User, Database, BarChart3, Zap, AlertCircle } from "lucide-react"
import { getMockSystemStats, getMockClients } from "@/lib/mock-data" // Import async functions

export default async function UserDashboard() {
  const user = await requireRole(["user"])
  const stats = await getMockSystemStats() // Fetch stats asynchronously
  const clients = await getMockClients() // Fetch clients asynchronously

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Users className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">User Dashboard</h1>
                <p className="text-sm text-gray-500">Welcome back, {user.firstName}</p>
              </div>
              <Badge variant="secondary">USER</Badge>
            </div>
            <form action={logoutAction}>
              <Button type="submit" variant="outline">
                Sign Out
              </Button>
            </form>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Limited Access Notice */}
          <div className="mb-6">
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">User Access Level</p>
                    <p className="text-sm text-blue-700">
                      You have read-only access to permits and analytics. You can manage client data and view automation
                      classes.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* User Profile Card */}
          <div className="mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <User className="h-8 w-8 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {user.firstName} {user.lastName}
                    </h3>
                    <p className="text-gray-500">{user.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="secondary">User Role</Badge>
                      <Badge variant="outline">{user.permissions.length} Module Access</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Limited Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Database className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Permits (View Only)</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_permits.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">Read-only access</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active Clients</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.active_clients}</p>
                    <p className="text-xs text-green-600">Can edit</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Zap className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Automation Classes</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.automation_classes}</p>
                    <p className="text-xs text-gray-500">View only</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Available Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="h-5 w-5 mr-2 text-green-600" />
                  Available Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full justify-start bg-transparent" variant="outline">
                  <Database className="h-4 w-4 mr-2" />
                  View Permit Database (Read Only)
                </Button>
                <Button className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  Manage Client Data
                </Button>
                <Button className="w-full justify-start bg-transparent" variant="outline">
                  <Zap className="h-4 w-4 mr-2" />
                  View Automation Classes (Read Only)
                </Button>
                <Button className="w-full justify-start bg-transparent" variant="outline">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Analytics (Read Only)
                </Button>
              </CardContent>
            </Card>

            {/* Recent Client Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Client Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {clients.slice(0, 3).map((client) => (
                    <div key={client.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <Users className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{client.name}</p>
                        <p className="text-xs text-gray-500">{client.company}</p>
                        <p className="text-xs text-gray-500">Status: {client.status}</p>
                      </div>
                      <Button size="sm" variant="outline">
                        Edit
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Restricted Areas Notice */}
            <Card className="lg:col-span-2 border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="flex items-center text-red-800">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  Restricted Access Areas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-red-800">No Access To:</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      <li>• System Settings</li>
                      <li>• Creating/Deleting Automation Classes</li>
                      <li>• Modifying Permit Data</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-semibold text-red-800">Limited Access To:</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      <li>• Permits (View Only)</li>
                      <li>• Analytics (View Only)</li>
                      <li>• Automation Classes (View Only)</li>
                      <li>• Email Templates (View Only)</li>
                    </ul>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-red-100 rounded-md">
                  <p className="text-sm text-red-800">
                    <strong>Need additional access?</strong> Contact your administrator to request permission changes or
                    role upgrades.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
