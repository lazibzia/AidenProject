import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { mockAdminUsers } from "./mock-data"
import type { AdminUser, AdminSession, AdminPermission } from "./types"

export async function createSession(user: AdminUser): Promise<void> {
  const session: AdminSession = {
    user,
    expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  }

  cookies().set("admin_session", JSON.stringify(session), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 7 * 24 * 60 * 60,
  })
}

export async function getSession(): Promise<AdminSession | null> {
  const sessionCookie = cookies().get("admin_session")

  if (!sessionCookie) {
    return null
  }

  try {
    const session: AdminSession = JSON.parse(sessionCookie.value)

    if (new Date(session.expires) < new Date()) {
      await destroySession()
      return null
    }

    return session
  } catch {
    return null
  }
}

export async function destroySession(): Promise<void> {
  cookies().delete("admin_session")
}

export async function requireAuth(): Promise<AdminUser> {
  const session = await getSession()

  if (!session) {
    redirect("/auth/login")
  }

  return session.user
}

export async function requireRole(roles: AdminUser["role"][]): Promise<AdminUser> {
  const user = await requireAuth()

  if (!roles.includes(user.role)) {
    redirect("/unauthorized")
  }

  return user
}

export async function requirePermission(
  module: AdminPermission["module"],
  action: AdminPermission["actions"][0],
): Promise<AdminUser> {
  const user = await requireAuth()

  const hasPermission = user.permissions.some(
    (permission) => permission.module === module && permission.actions.includes(action),
  )

  if (!hasPermission) {
    redirect("/unauthorized")
  }

  return user
}

export async function authenticateAdmin(email: string, password: string): Promise<AdminUser | null> {
  await new Promise((resolve) => setTimeout(resolve, 1000))

  const adminUser = mockAdminUsers.find((user) => user.email === email && user.password === password)

  if (adminUser && adminUser.status === "active") {
    const { password: _, ...userWithoutPassword } = adminUser

    // Update last login
    adminUser.last_login = new Date().toISOString().split("T")[0]

    return userWithoutPassword
  }

  return null
}

export async function registerAdmin(userData: {
  email: string
  password: string
  firstName: string
  lastName: string
  role: AdminUser["role"]
}): Promise<AdminUser> {
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Check if user already exists
  if (mockAdminUsers.find((user) => user.email === userData.email)) {
    throw new Error("User already exists")
  }

  const newUser: AdminUser & { password: string } = {
    id: Date.now().toString(),
    email: userData.email,
    firstName: userData.firstName,
    lastName: userData.lastName,
    role: userData.role,
    status: "pending", // New users start as pending
    created_date: new Date().toISOString().split("T")[0],
    last_login: "",
    password: userData.password,
    permissions: getDefaultPermissions(userData.role),
  }

  // Add to mock database
  mockAdminUsers.push(newUser)

  const { password: _, ...userWithoutPassword } = newUser
  return userWithoutPassword
}

export function getDefaultPermissions(role: AdminUser["role"]): AdminPermission[] {
  switch (role) {
    case "admin":
      return [
        { module: "permits", actions: ["read", "write", "delete", "admin"] },
        { module: "clients", actions: ["read", "write", "delete", "admin"] },
        { module: "automation", actions: ["read", "write", "delete", "admin"] },
        { module: "analytics", actions: ["read", "write", "delete", "admin"] },
        { module: "settings", actions: ["read", "write", "delete", "admin"] },
        // Removed { module: "users", actions: ["read", "write", "delete", "admin"] },
        { module: "data-sources", actions: ["read", "write", "delete", "admin"] }, // Admin has full access
      ]
    case "user":
      return [
        { module: "permits", actions: ["read"] },
        { module: "clients", actions: ["read", "write"] },
        { module: "automation", actions: ["read"] },
        { module: "analytics", actions: ["read"] },
        { module: "data-sources", actions: ["read"] }, // User has read-only access
      ]
    default:
      return []
  }
}
