import type React from "react"
import { UserSidebar } from "@/components/user-sidebar"

export default async function UserDashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-gray-100">
      <UserSidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
