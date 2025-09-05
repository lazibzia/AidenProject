"use client";

import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation"; // Import useRouter
import { loginAction } from "@/lib/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert"; // Import Alert components
import { Building2, Mail, Lock, AlertCircle, CheckCircle } from "lucide-react"; // Add AlertCircle, CheckCircle
import type { FormState } from "@/lib/types"; // Assuming FormState is defined in lib/types.ts

export default function LoginPage() {
  const router = useRouter(); // Initialize useRouter

  // Use useActionState to manage the form submission state
  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    loginAction,
    {
      error: undefined,
      success: undefined,
      fields: {}, // No specific fields needed for login form state
    }
  );

  // Effect to handle successful login and redirect
  useEffect(() => {
    if (state.success) {
      // Redirect to dashboard on successful login
      router.push("/dashboard"); // Or wherever your dashboard page is
    }
  }, [state.success, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Building2 className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-gray-900">Admin Login</h2>
          <p className="mt-2 text-sm text-gray-600">
            Access the Permit Lead Generation Platform
          </p>
        </div>
        <Card className="w-full">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center">
              Sign In
            </CardTitle>
            <CardDescription className="text-center">
              Enter your administrator credentials
            </CardDescription>
          </CardHeader>
          <form action={formAction}>
            {" "}
            {/* Use formAction from useActionState */}
            <CardContent className="space-y-4">
              {/* Display error message */}
              {state?.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{state.error}</AlertDescription>
                </Alert>
              )}
              {/* Display success message (though usually followed by redirect) */}
              {state?.success && (
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-700">
                    {state.success}
                  </AlertDescription>
                </Alert>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="admin@permitplatform.com"
                    className="pl-10"
                    required
                    disabled={isPending} // Disable input during submission
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="Enter your password"
                    className="pl-10"
                    required
                    disabled={isPending} // Disable input during submission
                  />
                </div>
              </div>
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                <p className="font-medium mb-1">Demo Credentials:</p>
                <p>Email: admin@permitplatform.com</p>
                <p>Password: admin123</p>
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "Signing In..." : "Sign In to Dashboard"}{" "}
                {/* Change button text based on pending state */}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
