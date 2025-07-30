"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { logoutAction } from "@/lib/actions"
import { Building2, LayoutDashboard, Database, Users, Zap, Settings, BarChart3, LogOut, Globe } from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Master Database", href: "/dashboard/permits", icon: Database },
  { name: "Data Sources", href: "/dashboard/data-sources", icon: Globe },
  { name: "Clients", href: "/dashboard/clients", icon: Users },
  { name: "Automation Classes", href: "/dashboard/automation", icon: Zap },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      <div className="flex items-center px-6 py-4 border-b">
        <Building2 className="h-8 w-8 text-blue-600" />
        <span className="ml-2 text-lg font-semibold text-gray-900">Permit Platform</span>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive ? "bg-blue-100 text-blue-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t">
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
