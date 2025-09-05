import { getSession } from "@/lib/auth"
import { redirect } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Building2, Users, Zap, BarChart3 } from "lucide-react"

export default async function HomePage() {
  const session = await getSession()

  if (session) {
    redirect("/dashboard")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">City Permit Lead Generation Platform</h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Aggregate, filter, and distribute city-issued permit data as qualified sales leads. Empower your business
            with targeted, automated lead generation from municipal permit databases.
          </p>
          <Link href="/auth/login">
            <Button size="lg" className="text-lg px-8 py-3">
              Access Dashboard
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          <Card className="text-center">
            <CardHeader>
              <Building2 className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <CardTitle>Data Aggregation</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Automatically pull permit data from multiple city sources daily</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Users className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <CardTitle>Client Management</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Manage client profiles and customize lead distribution preferences</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Zap className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <CardTitle>Automation Classes</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Create intelligent filtering rules and automated lead distribution</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <BarChart3 className="h-12 w-12 text-orange-600 mx-auto mb-4" />
              <CardTitle>Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Monitor system performance and lead distribution metrics</CardDescription>
            </CardContent>
          </Card>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">For System Administrators</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Master dashboard with all permit data</li>
                <li>• Advanced filtering and search capabilities</li>
                <li>• Client account management</li>
                <li>• Automation class configuration</li>
                <li>• Lead distribution rule setup</li>
                <li>• Email delivery monitoring</li>
              </ul>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-4">System Capabilities</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Daily automated data ingestion</li>
                <li>• Customizable email templates</li>
                <li>• Lead uniqueness engine</li>
                <li>• Territory-based distribution</li>
                <li>• Round-robin lead assignment</li>
                <li>• Exclusion rule management</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
