"use server"

import { redirect } from "next/navigation"
import { revalidatePath } from "next/cache"
import { authenticateAdmin, createSession, destroySession, registerAdmin } from "./auth"
import {
  addMockClient,
  updateMockClient,
  deleteMockClient,
  addMockAutomationClass,
  updateMockAutomationClass,
  deleteMockAutomationClass,
  toggleMockAutomationClassStatus, // This import is correct
  updateMockSystemConfiguration,
} from "./mock-data"
import type { AdminUser, FormState, Client, AutomationClass, SystemConfiguration } from "./types"

// Import AWS SES Client (conceptual, requires installation in a real project)
// import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";

// Placeholder for SES client initialization (replace with actual import and config)
const sesClient = {
  send: async (command: any) => {
    console.log("Simulating SES email send:", command.input)
    // In a real application, this would be:
    // const client = new SESClient({
    //   region: process.env.AWS_REGION,
    //   credentials: {
    //     accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    //     secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    //   },
    // });
    // return client.send(command);
    return { MessageId: `mock-email-${Date.now()}` } // Mock response
  },
}

export async function loginAction(previousState: FormState | undefined, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  try {
    const user = await authenticateAdmin(email, password)

    if (!user) {
      return { error: "Invalid credentials or account not active" }
    }

    await createSession(user)
    redirect("/dashboard")
  } catch (error) {
    return { error: "Login failed. Please try again." }
  }
}

export async function registerAction(previousState: FormState | undefined, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string
  const confirmPassword = formData.get("confirmPassword") as string
  const firstName = formData.get("firstName") as string
  const lastName = formData.get("lastName") as string
  const role = formData.get("role") as AdminUser["role"]

  if (!email || !password || !confirmPassword || !firstName || !lastName || !role) {
    return { error: "All fields are required" }
  }

  if (password !== confirmPassword) {
    return {
      error: "Passwords do not match",
      fields: { email, firstName, lastName }, // Return fields to retain
    }
  }

  if (password.length < 8) {
    return {
      error: "Password must be at least 8 characters long",
      fields: { email, firstName, lastName }, // Return fields to retain
    }
  }

  try {
    const user = await registerAdmin({
      email,
      password,
      firstName,
      lastName,
      role,
    })

    return { success: "Account created successfully. Please wait for admin approval." }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message, fields: { email, firstName, lastName } } // Return fields to retain
    }
    return { error: "Registration failed. Please try again.", fields: { email, firstName, lastName } } // Return fields to retain
  }
}

export async function logoutAction() {
  await destroySession()
  redirect("/auth/login")
}

export async function addClientAction(previousState: FormState | undefined, formData: FormData) {
  const name = formData.get("name") as string
  const email = formData.get("email") as string
  const company = formData.get("company") as string
  const phone = formData.get("phone") as string
  const city = formData.get("city") as string // New field
  const zip_code = formData.get("zip_code") as string // New field
  const status = formData.get("status") as Client["status"]

  if (!name || !email || !company || !phone || !city || !zip_code || !status) {
    return { error: "All fields are required.", fields: { name, email, company, phone, city, zip_code, status } }
  }

  try {
    addMockClient({ name, email, company, phone, city, zip_code, status })
    revalidatePath("/dashboard/clients")
    return { success: "Client added successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message, fields: { name, email, company, phone, city, zip_code, status } }
    }
    return { error: "Failed to add client.", fields: { name, email, company, phone, city, zip_code, status } }
  }
}

export async function updateClientAction(previousState: FormState | undefined, formData: FormData) {
  const id = formData.get("id") as string
  const name = formData.get("name") as string
  const email = formData.get("email") as string
  const company = formData.get("company") as string
  const phone = formData.get("phone") as string
  const city = formData.get("city") as string // New field
  const zip_code = formData.get("zip_code") as string // New field
  const status = formData.get("status") as Client["status"]

  if (!id || !name || !email || !company || !phone || !city || !zip_code || !status) {
    return { error: "All fields are required.", fields: { name, email, company, phone, city, zip_code, status } }
  }

  try {
    const updated = updateMockClient(id, { name, email, company, phone, city, zip_code, status })
    if (!updated) {
      return { error: "Client not found.", fields: { name, email, company, phone, city, zip_code, status } }
    }
    revalidatePath("/dashboard/clients")
    return { success: "Client updated successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message, fields: { name, email, company, phone, city, zip_code, status } }
    }
    return { error: "Failed to update client.", fields: { name, email, company, phone, city, zip_code, status } }
  }
}

export async function deleteClientAction(formData: FormData) {
  const id = formData.get("id") as string

  if (!id) {
    return { error: "Client ID is required for deletion." }
  }

  try {
    const deleted = deleteMockClient(id)
    if (!deleted) {
      return { error: "Client not found or could not be deleted." }
    }
    revalidatePath("/dashboard/clients")
    return { success: "Client deleted successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message }
    }
    return { error: "Failed to delete client." }
  }
}

export async function addAutomationClassAction(previousState: FormState | undefined, formData: FormData) {
  const client_id = formData.get("client_id") as string
  const name = formData.get("name") as string
  const description = formData.get("description") as string
  const status = formData.get("status") as AutomationClass["status"]
  const filters = JSON.parse(formData.get("filters") as string) // Assuming JSON string
  const distribution_rules = JSON.parse(formData.get("distribution_rules") as string) // Assuming JSON string
  const exclusion_rules = JSON.parse(formData.get("exclusion_rules") as string) // Assuming JSON string
  const email_template = JSON.parse(formData.get("email_template") as string) // Assuming JSON string

  if (!client_id || !name || !description || !status || !filters || !distribution_rules || !email_template) {
    return { error: "All fields are required." }
  }

  try {
    addMockAutomationClass({
      client_id,
      name,
      description,
      status,
      filters,
      distribution_rules,
      exclusion_rules,
      email_template,
    })
    revalidatePath("/dashboard/automation")
    return { success: "Automation class added successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message }
    }
    return { error: "Failed to add automation class." }
  }
}

export async function updateAutomationClassAction(previousState: FormState | undefined, formData: FormData) {
  const id = formData.get("id") as string
  const client_id = formData.get("client_id") as string
  const name = formData.get("name") as string
  const description = formData.get("description") as string
  const status = formData.get("status") as AutomationClass["status"]
  const filters = JSON.parse(formData.get("filters") as string) // Assuming JSON string
  const distribution_rules = JSON.parse(formData.get("distribution_rules") as string) // Assuming JSON string
  const exclusion_rules = JSON.parse(formData.get("exclusion_rules") as string) // Assuming JSON string
  const email_template = JSON.parse(formData.get("email_template") as string) // Assuming JSON string

  if (!id || !client_id || !name || !description || !status || !filters || !distribution_rules || !email_template) {
    return { error: "All fields are required." }
  }

  try {
    const updated = updateMockAutomationClass(id, {
      client_id,
      name,
      description,
      status,
      filters,
      distribution_rules,
      exclusion_rules,
      email_template,
    })
    if (!updated) {
      return { error: "Automation class not found." }
    }
    revalidatePath("/dashboard/automation")
    return { success: "Automation class updated successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message }
    }
    return { error: "Failed to update automation class." }
  }
}

export async function deleteAutomationClassAction(formData: FormData) {
  const id = formData.get("id") as string

  if (!id) {
    return { error: "Automation Class ID is required for deletion." }
  }

  try {
    const deleted = deleteMockAutomationClass(id)
    if (!deleted) {
      return { error: "Automation class not found or could not be deleted." }
    }
    revalidatePath("/dashboard/automation")
    return { success: "Automation class deleted successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message }
    }
    return { error: "Failed to delete automation class." }
  }
}

export async function toggleAutomationClassStatusAction(formData: FormData) {
  const id = formData.get("id") as string
  const currentStatus = formData.get("currentStatus") as AutomationClass["status"]
  const newStatus = currentStatus === "active" ? "inactive" : "active"

  if (!id || !currentStatus) {
    return { error: "Automation Class ID and current status are required." }
  }

  try {
    const updated = toggleMockAutomationClassStatus(id, newStatus)
    if (!updated) {
      return { error: "Automation class not found or status could not be toggled." }
    }
    revalidatePath("/dashboard/automation")
    return { success: `Automation class status changed to ${newStatus}!` }
  } catch (error) {
    if (error instanceof Error) {
      return { error: error.message }
    }
    return { error: "Failed to toggle automation class status." }
  }
}

export async function saveSystemSettingsAction(
  previousState: FormState | undefined,
  formData: FormData,
): Promise<FormState> {
  const section = formData.get("section") as keyof SystemConfiguration

  if (!section) {
    return { error: "Settings section is required." }
  }

  try {
    await new Promise((resolve) => setTimeout(resolve, 500)) // Simulate API call

    let updatedData: Partial<SystemConfiguration[typeof section]> = {}

    switch (section) {
      case "dataSource":
        updatedData = {
          austinApiEndpoint: formData.get("austinApiEndpoint") as string,
          ingestionFrequency: formData.get(
            "ingestionFrequency",
          ) as SystemConfiguration["dataSource"]["ingestionFrequency"],
          autoIngestionEnabled: formData.get("autoIngestionEnabled") === "on",
          dataValidationEnabled: formData.get("dataValidationEnabled") === "on",
        }
        break
      case "email":
        updatedData = {
          smtpServer: formData.get("smtpServer") as string,
          smtpPort: formData.get("smtpPort") as string,
          fromEmail: formData.get("fromEmail") as string,
          dailySendTime: formData.get("dailySendTime") as SystemConfiguration["email"]["dailySendTime"],
          emailNotificationsEnabled: formData.get("emailNotificationsEnabled") === "on",
        }
        break
      case "security":
        updatedData = {
          sessionTimeoutMinutes: Number.parseInt(formData.get("sessionTimeoutMinutes") as string),
          maxLoginAttempts: Number.parseInt(formData.get("maxLoginAttempts") as string),
          twoFactorEnabled: formData.get("twoFactorEnabled") === "on",
          auditLoggingEnabled: formData.get("auditLoggingEnabled") === "on",
        }
        break
      case "notifications":
        updatedData = {
          dataIngestionAlertsEnabled: formData.get("dataIngestionAlertsEnabled") === "on",
          emailDeliveryAlertsEnabled: formData.get("emailDeliveryAlertsEnabled") === "on",
          systemHealthAlertsEnabled: formData.get("systemHealthAlertsEnabled") === "on",
          clientActivityAlertsEnabled: formData.get("clientActivityAlertsEnabled") === "on",
          alertEmailAddress: formData.get("alertEmailAddress") as string,
        }
        break
      default:
        return { error: "Invalid settings section." }
    }

    updateMockSystemConfiguration(section, updatedData)
    revalidatePath("/dashboard/settings")
    return { success: `${section} settings saved successfully!` }
  } catch (error) {
    if (error instanceof Error) {
      return { error: `Failed to save ${section} settings: ${error.message}` }
    }
    return { error: `Failed to save ${section} settings.` }
  }
}

// New Server Actions for maintenance tasks
export async function runDatabaseCleanupAction(): Promise<FormState> {
  try {
    await new Promise((resolve) => setTimeout(resolve, 2000)) // Simulate 2-second cleanup
    revalidatePath("/dashboard/settings")
    return { success: "Database cleanup completed successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: `Database cleanup failed: ${error.message}` }
    }
    return { error: "Database cleanup failed." }
  }
}

export async function runSystemBackupAction(): Promise<FormState> {
  try {
    await new Promise((resolve) => setTimeout(resolve, 3000)) // Simulate 3-second backup
    revalidatePath("/dashboard/settings")
    return { success: "System backup completed successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: `System backup failed: ${error.message}` }
    }
    return { error: "System backup failed." }
  }
}

export async function generatePerformanceReportAction(): Promise<FormState> {
  try {
    await new Promise((resolve) => setTimeout(resolve, 1500)) // Simulate 1.5-second report generation
    revalidatePath("/dashboard/settings")
    return { success: "Performance report generated successfully!" }
  } catch (error) {
    if (error instanceof Error) {
      return { error: `Performance report generation failed: ${error.message}` }
    }
    return { error: "Performance report generation failed." }
  }
}

export async function sendLeadEmail(
  toEmail: string,
  subject: string,
  bodyHtml: string,
  bodyText: string,
): Promise<FormState> {
  // Ensure environment variables are set in your Vercel project
  const FROM_EMAIL = process.env.SES_FROM_EMAIL
  if (!FROM_EMAIL) {
    return { error: "SES_FROM_EMAIL environment variable is not configured." }
  }

  const params = {
    Destination: {
      ToAddresses: [toEmail],
    },
    Message: {
      Body: {
        Html: {
          Charset: "UTF-8",
          Data: bodyHtml,
        },
        Text: {
          Charset: "UTF-8",
          Data: bodyText,
        },
      },
      Subject: {
        Charset: "UTF-8",
        Data: subject,
      },
    },
    Source: FROM_EMAIL,
  }

  try {
    // In a real application, you would use:
    // const command = new SendEmailCommand(params);
    // await sesClient.send(command);
    await sesClient.send({ input: params }) // Using mock client
    console.log(`Email sent to ${toEmail} with subject: ${subject}`)
    return { success: `Email successfully sent to ${toEmail}!` }
  } catch (error) {
    console.error("Error sending email with SES:", error)
    if (error instanceof Error) {
      return { error: `Failed to send email: ${error.message}` }
    }
    return { error: "Failed to send email." }
  }
}
