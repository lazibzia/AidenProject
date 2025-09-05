"use client"

import { useActionState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Mail, Phone, Building2, User, AlertCircle, CheckCircle, MapPin } from "lucide-react" // Added MapPin
import { addClientAction, updateClientAction } from "@/lib/actions"
import type { Client, FormState } from "@/lib/types"

interface ClientFormProps {
  client?: Client // Optional client prop for editing
  onSuccess?: () => void // Callback for successful submission
}

export function ClientForm({ client, onSuccess }: ClientFormProps) {
  const isEditing = !!client
  const action = isEditing ? updateClientAction : addClientAction
  const [state, formAction, isPending] = useActionState<FormState, FormData>(action, {
    error: undefined,
    success: undefined,
    fields: {
      name: client?.name || "",
      email: client?.email || "",
      company: client?.company || "",
      phone: client?.phone || "",
      city: client?.city || "", // Initialize new field
      zip_code: client?.zip_code || "", // Initialize new field
      status: client?.status || "active",
    },
  })

  useEffect(() => {
    if (state.success) {
      onSuccess?.()
    }
  }, [state.success, onSuccess])

  return (
    <form action={formAction} className="space-y-4">
      {state?.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      {state?.success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700">{state.success}</AlertDescription>
        </Alert>
      )}

      {isEditing && <input type="hidden" name="id" value={client.id} />}

      <div className="space-y-2">
        <Label htmlFor="name">Client Name</Label>
        <div className="relative">
          <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="name"
            name="name"
            type="text"
            placeholder="John Doe"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.name}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <div className="relative">
          <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="client@example.com"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.email}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="company">Company</Label>
        <div className="relative">
          <Building2 className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="company"
            name="company"
            type="text"
            placeholder="ABC Corp"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.company}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Phone</Label>
        <div className="relative">
          <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="phone"
            name="phone"
            type="tel"
            placeholder="(555) 123-4567"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.phone}
          />
        </div>
      </div>

      {/* New City Field */}
      <div className="space-y-2">
        <Label htmlFor="city">City</Label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="city"
            name="city"
            type="text"
            placeholder="Austin"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.city}
          />
        </div>
      </div>

      {/* New Zip Code Field */}
      <div className="space-y-2">
        <Label htmlFor="zip_code">Zip Code</Label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            id="zip_code"
            name="zip_code"
            type="text"
            placeholder="78701"
            className="pl-10"
            required
            disabled={isPending}
            defaultValue={state.fields?.zip_code}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select name="status" required defaultValue={state.fields?.status}>
          <SelectTrigger>
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? (isEditing ? "Saving..." : "Adding...") : isEditing ? "Save Changes" : "Add Client"}
      </Button>
    </form>
  )
}
