"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { mockAutomationClasses, mockClients } from "@/lib/mock-data"
import type { AutomationClass } from "@/lib/types"
import { Plus, Search, Edit, Trash2, Play, Pause } from "lucide-react"
import { AutomationClassForm } from "@/components/automation-class-form"
import { deleteAutomationClassAction, toggleAutomationClassStatusAction } from "@/lib/actions"

export default function AutomationPage() {
  const router = useRouter()
  const [automationClasses, setAutomationClasses] = useState<AutomationClass[]>(mockAutomationClasses)
  const [searchTerm, setSearchTerm] = useState("")
  const [isAutomationClassDialogOpen, setIsAutomationClassDialogOpen] = useState(false)
  const [editingAutomationClass, setEditingAutomationClass] = useState<AutomationClass | null>(null)

  const filteredClasses = automationClasses.filter(
    (ac) =>
      ac.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ac.description.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getClientName = (clientId: string) => {
    const client = mockClients.find((c) => c.id === clientId)
    return client ? client.name : "Unknown Client"
  }

  const handleAutomationClassFormSuccess = () => {
    setIsAutomationClassDialogOpen(false)
    setEditingAutomationClass(null)
    setAutomationClasses([...mockAutomationClasses]) // Update local state
    router.refresh() // Revalidate data after successful add/edit
  }

  const handleDelete = async (classId: string) => {
    if (window.confirm("Are you sure you want to delete this automation class?")) {
      const formData = new FormData()
      formData.append("id", classId)
      const result = await deleteAutomationClassAction(formData)
      if (result?.success) {
        setAutomationClasses([...mockAutomationClasses]) // Update local state
        router.refresh() // Revalidate data after successful delete
      } else if (result?.error) {
        alert(result.error)
      }
    }
  }

  const handleToggleStatus = async (classId: string, currentStatus: AutomationClass["status"]) => {
    const formData = new FormData()
    formData.append("id", classId)
    formData.append("currentStatus", currentStatus)
    const result = await toggleAutomationClassStatusAction(formData)
    if (result?.success) {
      setAutomationClasses([...mockAutomationClasses]) // Update local state
      router.refresh() // Revalidate data after successful toggle
    } else if (result?.error) {
      alert(result.error)
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Automation Classes</h1>
          <p className="text-gray-600">Configure automated lead generation and distribution rules</p>
        </div>
        <Dialog open={isAutomationClassDialogOpen} onOpenChange={setIsAutomationClassDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center" onClick={() => setEditingAutomationClass(null)}>
              <Plus className="h-4 w-4 mr-2" />
              Create New Class
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>
                {editingAutomationClass ? "Edit Automation Class" : "Create New Automation Class"}
              </DialogTitle>
              <DialogDescription>
                {editingAutomationClass
                  ? "Make changes to the automation class details here."
                  : "Fill in the details for the new automation class."}
              </DialogDescription>
            </DialogHeader>
            <AutomationClassForm
              key={editingAutomationClass?.id || "new-automation-class"}
              automationClass={editingAutomationClass || undefined}
              onSuccess={handleAutomationClassFormSuccess}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search automation classes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Automation Classes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredClasses.map((automationClass) => (
          <Card key={automationClass.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{automationClass.name}</CardTitle>
                  <CardDescription>{automationClass.description}</CardDescription>
                </div>
                <Badge variant={automationClass.status === "active" ? "default" : "secondary"}>
                  {automationClass.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-500">Client:</span>
                    <p>{getClientName(automationClass.client_id)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Last Run:</span>
                    <p>{automationClass.last_run}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Leads Today:</span>
                    <p className="font-semibold text-blue-600">{automationClass.leads_sent_today}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Created:</span>
                    <p>{automationClass.created_date}</p>
                  </div>
                </div>

                <div>
                  <span className="font-medium text-gray-500 text-sm">Active Filters:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {automationClass.filters.slice(0, 3).map((filter, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {filter.field}: {filter.operator}{" "}
                        {Array.isArray(filter.value) ? filter.value.join(", ") : String(filter.value)}
                      </Badge>
                    ))}
                    {automationClass.filters.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{automationClass.filters.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                <div>
                  <span className="font-medium text-gray-500 text-sm">Distribution:</span>
                  <p className="text-sm capitalize">{automationClass.distribution_rules.type.replace("_", " ")}</p>
                </div>

                <div className="flex space-x-2 pt-2 border-t">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 bg-transparent"
                    onClick={() => {
                      setEditingAutomationClass(automationClass)
                      setIsAutomationClassDialogOpen(true)
                    }}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleToggleStatus(automationClass.id, automationClass.status)}
                  >
                    {automationClass.status === "active" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-red-600 hover:text-red-700 bg-transparent"
                    onClick={() => handleDelete(automationClass.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredClasses.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500">No automation classes found matching your search.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
