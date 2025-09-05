import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const sessionCookie = request.cookies.get("admin_session")
  const { pathname } = request.nextUrl

  const publicRoutes = ["/auth/login", "/auth/register", "/"]
  const isPublicRoute = publicRoutes.includes(pathname)

  if (!sessionCookie && !isPublicRoute) {
    return NextResponse.redirect(new URL("/auth/login", request.url))
  }

  if (sessionCookie && (pathname === "/auth/login" || pathname === "/auth/register" || pathname === "/")) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
