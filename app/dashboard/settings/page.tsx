"use client"

import { useState, useEffect } from "react"
import { useActionState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Settings, Shield, Bell, AlertCircle, CheckCircle } from "lucide-react"
import { mockSystemConfiguration } from "@/lib/mock-data"
import {
  saveSystemSettingsAction,
  runDatabaseCleanupAction,
  runSystemBackupAction,
  generatePerformanceReportAction,
} from "@/lib/actions"
import type { FormState, SystemConfiguration } from "@/lib/types"

export default function SettingsPage() {
  const [dataSourceState, dataSourceAction, isDataSourcePending] = useActionState<FormState, FormData>(
    saveSystemSettingsAction,
    {},
  )
  const [securityState, securityAction, isSecurityPending] = useActionState<FormState, FormData>(
    saveSystemSettingsAction,
    {},
  )
  const [notificationsState, notificationsAction, isNotificationsPending] = useActionState<FormState, FormData>(
    saveSystemSettingsAction,
    {},
  )

  const [cleanupState, cleanupAction, isCleanupPending] = useActionState<FormState, FormData>(
    runDatabaseCleanupAction,
    {},
  )
  const [backupState, backupAction, isBackupPending] = useActionState<FormState, FormData>(runSystemBackupAction, {})
  const [reportState, reportAction, isReportPending] = useActionState<FormState, FormData>(
    generatePerformanceReportAction,
    {},
  )

  const [currentSettings, setCurrentSettings] = useState<SystemConfiguration>(mockSystemConfiguration)

  useEffect(() => {
    setCurrentSettings(mockSystemConfiguration)
  }, [mockSystemConfiguration])

  const handleDataSourceSubmit = (formData: FormData) => {
    formData.append("section", "dataSource")
    dataSourceAction(formData)
  }

  const handleSecuritySubmit = (formData: FormData) => {
    formData.append("section", "security")
    securityAction(formData)
  }

  const handleNotificationsSubmit = (formData: FormData) => {
    formData.append("section", "notifications")
    notificationsAction(formData)
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
        <p className="text-gray-600">Configure system-wide settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Security & Access
            </CardTitle>
            <CardDescription>Manage system security and access control settings</CardDescription>
          </CardHeader>
          <form action={handleSecuritySubmit}>
            <CardContent className="space-y-4">
              {securityState?.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{securityState.error}</AlertDescription>
                </Alert>
              )}
              {securityState?.success && (
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-700">{securityState.success}</AlertDescription>
                </Alert>
              )}
              <div>
                <Label htmlFor="session-timeout">Session Timeout (minutes)</Label>
                <Input
                  id="session-timeout"
                  name="sessionTimeoutMinutes"
                  type="number"
                  defaultValue={currentSettings.security.sessionTimeoutMinutes}
                  className="mt-1"
                  disabled={isSecurityPending}
                />
              </div>

              <div>
                <Label htmlFor="max-login-attempts">Max Login Attempts</Label>
                <Input
                  id="max-login-attempts"
                  name="maxLoginAttempts"
                  type="number"
                  defaultValue={currentSettings.security.maxLoginAttempts}
                  className="mt-1"
                  disabled={isSecurityPending}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="two-factor"
                  name="twoFactorEnabled"
                  defaultChecked={currentSettings.security.twoFactorEnabled}
                  disabled={isSecurityPending}
                />
                <Label htmlFor="two-factor">Enable two-factor authentication</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="audit-logging"
                  name="auditLoggingEnabled"
                  defaultChecked={currentSettings.security.auditLoggingEnabled}
                  disabled={isSecurityPending}
                />
                <Label htmlFor="audit-logging">Enable audit logging</Label>
              </div>

              <Button type="submit" className="w-full" disabled={isSecurityPending}>
                {isSecurityPending ? "Saving..." : "Save Security Settings"}
              </Button>
            </CardContent>
          </form>
        </Card>

        {/* System Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              System Notifications
            </CardTitle>
            <CardDescription>Configure system alerts and notification preferences</CardDescription>
          </CardHeader>
          <form action={handleNotificationsSubmit}>
            <CardContent className="space-y-4">
              {notificationsState?.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{notificationsState.error}</AlertDescription>
                </Alert>
              )}
              {notificationsState?.success && (
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-700">{notificationsState.success}</AlertDescription>
                </Alert>
              )}
              <div className="flex items-center space-x-2">
                <Switch
                  id="data-ingestion-alerts"
                  name="dataIngestionAlertsEnabled"
                  defaultChecked={currentSettings.notifications.dataIngestionAlertsEnabled}
                  disabled={isNotificationsPending}
                />
                <Label htmlFor="data-ingestion-alerts">Data ingestion failure alerts</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="email-delivery-alerts"
                  name="emailDeliveryAlertsEnabled"
                  defaultChecked={currentSettings.notifications.emailDeliveryAlertsEnabled}
                  disabled={isNotificationsPending}
                />
                <Label htmlFor="email-delivery-alerts">Email delivery failure alerts</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="system-health-alerts"
                  name="systemHealthAlertsEnabled"
                  defaultChecked={currentSettings.notifications.systemHealthAlertsEnabled}
                  disabled={isNotificationsPending}
                />
                <Label htmlFor="system-health-alerts">System health alerts</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="client-activity-alerts"
                  name="clientActivityAlertsEnabled"
                  defaultChecked={currentSettings.notifications.clientActivityAlertsEnabled}
                  disabled={isNotificationsPending}
                />
                <Label htmlFor="client-activity-alerts">Client activity notifications</Label>
              </div>

              <div>
                <Label htmlFor="alert-email">Alert Email Address</Label>
                <Input
                  id="alert-email"
                  name="alertEmailAddress"
                  defaultValue={currentSettings.notifications.alertEmailAddress}
                  className="mt-1"
                  disabled={isNotificationsPending}
                />
              </div>

              <Button type="submit" className="w-full" disabled={isNotificationsPending}>
                {isNotificationsPending ? "Saving..." : "Save Notification Settings"}
              </Button>
            </CardContent>
          </form>
        </Card>

        {/* System Maintenance */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              System Maintenance
            </CardTitle>
            <CardDescription>Database maintenance and system optimization tools</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <h4 className="font-semibold mb-2">Database Cleanup</h4>
                  <p className="text-sm text-gray-600 mb-4">Remove old permit records and optimize database</p>
                  <form action={cleanupAction}>
                    <Button
                      type="submit"
                      variant="outline"
                      className="w-full bg-transparent"
                      disabled={isCleanupPending}
                    >
                      {isCleanupPending ? "Running..." : "Run Cleanup"}
                    </Button>
                  </form>
                  {cleanupState?.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{cleanupState.error}</AlertDescription>
                    </Alert>
                  )}
                  {cleanupState?.success && (
                    <Alert className="border-green-200 bg-green-50 mt-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-700">{cleanupState.success}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 text-center">
                  <h4 className="font-semibold mb-2">System Backup</h4>
                  <p className="text-sm text-gray-600 mb-4">Create full system backup including all data</p>
                  <form action={backupAction}>
                    <Button
                      type="submit"
                      variant="outline"
                      className="w-full bg-transparent"
                      disabled={isBackupPending}
                    >
                      {isBackupPending ? "Creating..." : "Create Backup"}
                    </Button>
                  </form>
                  {backupState?.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{backupState.error}</AlertDescription>
                    </Alert>
                  )}
                  {backupState?.success && (
                    <Alert className="border-green-200 bg-green-50 mt-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-700">{backupState.success}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 text-center">
                  <h4 className="font-semibold mb-2">Performance Report</h4>
                  <p className="text-sm text-gray-600 mb-4">Generate detailed system performance report</p>
                  <form action={reportAction}>
                    <Button
                      type="submit"
                      variant="outline"
                      className="w-full bg-transparent"
                      disabled={isReportPending}
                    >
                      {isReportPending ? "Generating..." : "Generate Report"}
                    </Button>
                  </form>
                  {reportState?.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{reportState.error}</AlertDescription>
                    </Alert>
                  )}
                  {reportState?.success && (
                    <Alert className="border-green-200 bg-green-50 mt-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-700">{reportState.success}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-2">Maintenance Schedule</h4>
              <p className="text-sm text-yellow-700">
                Next scheduled maintenance: {currentSettings.maintenance.nextScheduledMaintenance}
              </p>
              <p className="text-sm text-yellow-700">
                Estimated downtime: {currentSettings.maintenance.estimatedDowntime}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
