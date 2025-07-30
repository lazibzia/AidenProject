import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { mockSystemStats, mockAutomationClasses } from "@/lib/mock-data"
import { BarChart3, TrendingUp, Mail, Users, Zap, AlertCircle } from "lucide-react"

export default function AnalyticsPage() {
  const stats = mockSystemStats

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
        <p className="text-gray-600">Monitor system performance and lead distribution metrics</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Mail className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Emails Sent (Today)</p>
                <p className="text-2xl font-bold text-gray-900">{stats.emails_sent_today}</p>
                <p className="text-xs text-green-600">+12% from yesterday</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Lead Conversion</p>
                <p className="text-2xl font-bold text-gray-900">87%</p>
                <p className="text-xs text-green-600">+5% this week</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Clients</p>
                <p className="text-2xl font-bold text-gray-900">{stats.active_clients}</p>
                <p className="text-xs text-blue-600">2 new this month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">System Health</p>
                <p className="text-2xl font-bold text-gray-900">{stats.system_uptime}</p>
                <p className="text-xs text-green-600">Excellent</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2" />
              Performance Overview
            </CardTitle>
            <CardDescription>System performance metrics for the last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Data Ingestion Success Rate</span>
                <span className="text-sm font-bold text-green-600">99.8%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: "99.8%" }}></div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Email Delivery Rate</span>
                <span className="text-sm font-bold text-blue-600">98.5%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: "98.5%" }}></div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Filter Processing Speed</span>
                <span className="text-sm font-bold text-purple-600">95.2%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{ width: "95.2%" }}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Performing Classes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Top Performing Classes
            </CardTitle>
            <CardDescription>Automation classes with highest lead generation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockAutomationClasses
                .sort((a, b) => b.leads_sent_today - a.leads_sent_today)
                .slice(0, 5)
                .map((automationClass, index) => (
                  <div key={automationClass.id} className="flex items-center space-x-4">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-blue-600">#{index + 1}</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{automationClass.name}</p>
                      <p className="text-xs text-gray-500">Last run: {automationClass.last_run}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-sm">{automationClass.leads_sent_today}</p>
                      <p className="text-xs text-gray-500">leads today</p>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent System Activity</CardTitle>
            <CardDescription>Latest system events and notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Daily data ingestion completed successfully</p>
                  <p className="text-xs text-gray-500">23 new permits processed from Austin, TX</p>
                </div>
                <span className="text-xs text-gray-500">2 minutes ago</span>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Automation class "Commercial Demolition" executed</p>
                  <p className="text-xs text-gray-500">3 leads sent to Austin Waste Management</p>
                </div>
                <span className="text-xs text-gray-500">15 minutes ago</span>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">New client account created</p>
                  <p className="text-xs text-gray-500">Wilson Contracting added to system</p>
                </div>
                <span className="text-xs text-gray-500">1 hour ago</span>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">System maintenance completed</p>
                  <p className="text-xs text-gray-500">Database optimization and backup completed</p>
                </div>
                <span className="text-xs text-gray-500">3 hours ago</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
