"use client"

import type React from "react"

import { useActionState, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, CheckCircle } from "lucide-react"
import { addAutomationClassAction, updateAutomationClassAction } from "@/lib/actions"
import type { AutomationClass, FormState, Client } from "@/lib/types"
import { mockClients } from "@/lib/mock-data" // To populate client dropdown

interface AutomationClassFormProps {
  automationClass?: AutomationClass // Optional prop for editing
  onSuccess?: () => void // Callback for successful submission
}

export function AutomationClassForm({ automationClass, onSuccess }: AutomationClassFormProps) {
  const isEditing = !!automationClass
  const action = isEditing ? updateAutomationClassAction : addAutomationClassAction

  // Initialize form state with existing data or defaults
  const [formState, formAction, isPending] = useActionState<FormState, FormData>(action, {
    error: undefined,
    success: undefined,
    fields: {
      client_id: automationClass?.client_id || "",
      name: automationClass?.name || "",
      description: automationClass?.description || "",
      status: automationClass?.status || "active",
      filters: JSON.stringify(automationClass?.filters || [], null, 2),
      distribution_rules: JSON.stringify(automationClass?.distribution_rules || {}, null, 2),
      exclusion_rules: JSON.stringify(automationClass?.exclusion_rules || [], null, 2),
      email_template: JSON.stringify(automationClass?.email_template || {}, null, 2),
    },
  })

  // State for local form inputs, especially for JSON fields
  const [clientId, setClientId] = useState(formState.fields?.client_id || "")
  const [name, setName] = useState(formState.fields?.name || "")
  const [description, setDescription] = useState(formState.fields?.description || "")
  const [status, setStatus] = useState(formState.fields?.status || "active")
  const [filtersJson, setFiltersJson] = useState(formState.fields?.filters || "")
  const [distributionRulesJson, setDistributionRulesJson] = useState(formState.fields?.distribution_rules || "")
  const [exclusionRulesJson, setExclusionRulesJson] = useState(formState.fields?.exclusion_rules || "")
  const [emailTemplateJson, setEmailTemplateJson] = useState(formState.fields?.email_template || "")

  useEffect(() => {
    if (formState.success) {
      onSuccess?.()
    }
  }, [formState.success, onSuccess])

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    // Manually add JSON stringified values to FormData
    formData.set("filters", filtersJson)
    formData.set("distribution_rules", distributionRulesJson)
    formData.set("exclusion_rules", exclusionRulesJson)
    formData.set("email_template", emailTemplateJson)

    // If editing, ensure the ID is present
    if (isEditing && automationClass?.id) {
      formData.set("id", automationClass.id)
    }

    formAction(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {formState?.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{formState.error}</AlertDescription>
        </Alert>
      )}

      {formState?.success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700">{formState.success}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="client_id">Client</Label>
        <Select name="client_id" required value={clientId} onValueChange={setClientId} disabled={isPending}>
          <SelectTrigger>
            <SelectValue placeholder="Select client" />
          </SelectTrigger>
          <SelectContent>
            {mockClients.map((client: Client) => (
              <SelectItem key={client.id} value={client.id}>
                {client.name} ({client.company})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Class Name</Label>
        <Input
          id="name"
          name="name"
          type="text"
          placeholder="e.g., Commercial Demolition Leads"
          required
          disabled={isPending}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          placeholder="e.g., Demolition permits for commercial properties over $50k"
          required
          disabled={isPending}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select name="status" required value={status} onValueChange={setStatus} disabled={isPending}>
          <SelectTrigger>
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="filters">Filters (JSON Array)</Label>
        <Textarea
          id="filters"
          name="filters"
          placeholder={`[{"field": "permit_type_desc", "operator": "contains", "value": "Demolition"}]`}
          required
          disabled={isPending}
          value={filtersJson}
          onChange={(e) => setFiltersJson(e.target.value)}
          rows={5}
        />
        <p className="text-xs text-gray-500">Enter as a JSON array of FilterRule objects.</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="distribution_rules">Distribution Rules (JSON Object)</Label>
        <Textarea
          id="distribution_rules"
          name="distribution_rules"
          placeholder={`{"type": "territory", "config": {"territories": ["78701"]}}`}
          required
          disabled={isPending}
          value={distributionRulesJson}
          onChange={(e) => setDistributionRulesJson(e.target.value)}
          rows={5}
        />
        <p className="text-xs text-gray-500">Enter as a JSON object of DistributionRule.</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="exclusion_rules">Exclusion Rules (JSON Array)</Label>
        <Textarea
          id="exclusion_rules"
          name="exclusion_rules"
          placeholder={`[{"field": "contractor_name", "operator": "contains", "value": "Competitor"}]`}
          disabled={isPending}
          value={exclusionRulesJson}
          onChange={(e) => setExclusionRulesJson(e.target.value)}
          rows={5}
        />
        <p className="text-xs text-gray-500">Optional. Enter as a JSON array of ExclusionRule objects.</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="email_template">Email Template (JSON Object)</Label>
        <Textarea
          id="email_template"
          name="email_template"
          placeholder={`{"subject": "Daily Leads", "body": "Here are your leads.", "format": "xlsx"}`}
          required
          disabled={isPending}
          value={emailTemplateJson}
          onChange={(e) => setEmailTemplateJson(e.target.value)}
          rows={5}
        />
        <p className="text-xs text-gray-500">Enter as a JSON object of EmailTemplate.</p>
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? (isEditing ? "Saving..." : "Adding...") : isEditing ? "Save Changes" : "Create Class"}
      </Button>
    </form>
  )
}
