"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { logoutAction } from "@/lib/actions"
import { Building2, LayoutDashboard, Database, Users, Zap, BarChart3, LogOut, Lock, Globe } from "lucide-react"

const userNavigation = [
  { name: "Dashboard", href: "/dashboard/user", icon: LayoutDashboard, access: "full" },
  { name: "Permit Database", href: "/dashboard/permits", icon: Database, access: "read-only" },
  { name: "Data Sources", href: "/dashboard/data-sources", icon: Globe, access: "read-only" },
  { name: "Client Management", href: "/dashboard/clients", icon: Users, access: "full" },
  { name: "Automation Classes", href: "/dashboard/automation", icon: Zap, access: "read-only" },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3, access: "read-only" },
]

export function UserSidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      <div className="flex items-center px-6 py-4 border-b">
        <Building2 className="h-8 w-8 text-blue-600" />
        <span className="ml-2 text-lg font-semibold text-gray-900">Permit Platform</span>
      </div>

      <div className="px-4 py-3 bg-green-50 border-b">
        <div className="flex items-center space-x-2">
          <Users className="h-4 w-4 text-green-600" />
          <Badge variant="secondary" className="text-xs">
            USER ACCESS
          </Badge>
        </div>
        <p className="text-xs text-green-700 mt-1">Limited permissions</p>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {userNavigation.map((item) => {
          const isActive = pathname === item.href
          const isReadOnly = item.access === "read-only"

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors relative",
                isActive ? "bg-blue-100 text-blue-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              <span className="flex-1">{item.name}</span>
              {isReadOnly && <Lock className="h-3 w-3 text-gray-400" />}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t">
        <div className="mb-3 p-2 bg-yellow-50 rounded-md">
          <p className="text-xs text-yellow-800">
            <strong>Need more access?</strong> Contact your administrator.
          </p>
        </div>
        <form action={logoutAction}>
          <Button type="submit" variant="ghost" className="w-full justify-start">
            <LogOut className="mr-3 h-5 w-5" />
            Sign Out
          </Button>
        </form>
      </div>
    </div>
  )
}
