import { requireRole } from "@/lib/auth"
import { logoutAction } from "@/lib/actions"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, User, Mail, Settings, HelpCircle, Bell } from "lucide-react"

export default async function GuestDashboard() {
  const user = await requireRole("guest")

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Users className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Guest Dashboard</h1>
                <p className="text-sm text-gray-500">Welcome, {user.firstName}</p>
              </div>
              <Badge variant="secondary">GUEST</Badge>
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
                    <Badge variant="secondary" className="mt-1">
                      Guest User
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="h-5 w-5 mr-2 text-blue-600" />
                  Profile Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">Update your personal information and preferences</p>
                <Button className="w-full">
                  <Settings className="h-4 w-4 mr-2" />
                  Edit Profile
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Mail className="h-5 w-5 mr-2 text-green-600" />
                  Messages
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">View your messages and notifications</p>
                <Button className="w-full bg-transparent" variant="outline">
                  <Mail className="h-4 w-4 mr-2" />
                  View Messages
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bell className="h-5 w-5 mr-2 text-purple-600" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">Manage your notification preferences</p>
                <Button className="w-full bg-transparent" variant="outline">
                  <Bell className="h-4 w-4 mr-2" />
                  Settings
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <HelpCircle className="h-5 w-5 mr-2 text-orange-600" />
                  Help & Support
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">Get help and contact our support team</p>
                <Button className="w-full bg-transparent" variant="outline">
                  <HelpCircle className="h-4 w-4 mr-2" />
                  Get Help
                </Button>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Available Services</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Button variant="outline" className="h-auto p-4 flex flex-col items-start bg-transparent">
                    <div className="font-semibold">Service A</div>
                    <div className="text-sm text-gray-500 mt-1">Access to basic features</div>
                  </Button>
                  <Button variant="outline" className="h-auto p-4 flex flex-col items-start bg-transparent">
                    <div className="font-semibold">Service B</div>
                    <div className="text-sm text-gray-500 mt-1">Guest-specific tools</div>
                  </Button>
                  <Button variant="outline" className="h-auto p-4 flex flex-col items-start bg-transparent">
                    <div className="font-semibold">Service C</div>
                    <div className="text-sm text-gray-500 mt-1">Community features</div>
                  </Button>
                  <Button variant="outline" className="h-auto p-4 flex flex-col items-start bg-transparent">
                    <div className="font-semibold">Service D</div>
                    <div className="text-sm text-gray-500 mt-1">Resource library</div>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
