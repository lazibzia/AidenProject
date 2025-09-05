import { getSession } from "@/lib/auth"
import { redirect } from "next/navigation"

export default async function DashboardRouter() {
  const session = await getSession()

  if (!session) {
    redirect("/auth/login")
  }

  if (session.user.role === "admin") {
    redirect("/dashboard/admin")
  } else if (session.user.role === "user") {
    redirect("/dashboard/user")
  } else {
    // Fallback for unexpected roles, or if a new role is introduced
    redirect("/unauthorized")
  }
}
