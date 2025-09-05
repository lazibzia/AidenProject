export interface Permit {
  id: string
  permit_type_desc: string
  applied_date: string
  issue_date: string
  address: string
  zip_code: string
  council_district: string
  contractor_name: string
  contractor_category: string
  contractor_phone: string
  work_class_group: string
  project_description: string
  valuation: number
  square_footage: number
  status: "active" | "completed" | "cancelled"
}

export interface Client {
  id: string
  name: string
  email: string
  company: string
  phone: string
  city: string // New field
  zip_code: string // New field
  created_date: string
  status: "active" | "inactive"
  automation_classes: AutomationClass[]
}

export interface AutomationClass {
  id: string
  client_id: string
  name: string
  description: string
  filters: FilterRule[]
  distribution_rules: DistributionRule
  exclusion_rules: ExclusionRule[]
  email_template: EmailTemplate
  status: "active" | "inactive"
  created_date: string
  last_run: string
  leads_sent_today: number
}

export interface FilterRule {
  field: string
  operator: "equals" | "contains" | "greater_than" | "less_than" | "in_list" | "date_range"
  value: string | string[] | { start: string; end: string }
}

export interface DistributionRule {
  type: "round_robin" | "territory" | "percentage"
  config: {
    territories?: string[]
    percentage?: number
    priority?: number
  }
}

export interface ExclusionRule {
  field: string
  operator: "equals" | "contains"
  value: string
}

export interface EmailTemplate {
  subject: string
  body: string
  format: "xlsx" | "csv"
}

export interface SystemStats {
  total_permits: number
  permits_today: number
  active_clients: number
  automation_classes: number
  emails_sent_today: number
  system_uptime: string
}

export interface AdminUser {
  id: string
  email: string
  firstName: string
  lastName: string
  role: "admin" | "user"
  status: "active" | "inactive" | "pending"
  created_date: string
  last_login: string
  permissions: AdminPermission[]
}

export interface AdminPermission {
  module: "permits" | "clients" | "automation" | "analytics" | "settings" | "data-sources" // Removed "users"
  actions: ("read" | "write" | "delete" | "admin")[]
}

export interface AdminSession {
  user: AdminUser
  expires: string
}

// New interface for System Configuration
export interface SystemConfiguration {
  dataSource: {
    austinApiEndpoint: string
    ingestionFrequency: "hourly" | "daily" | "weekly" | "monthly"
    autoIngestionEnabled: boolean
    dataValidationEnabled: boolean
  }
  email: {
    smtpServer: string
    smtpPort: string
    fromEmail: string
    dailySendTime: string
    emailNotificationsEnabled: boolean
  }
  security: {
    sessionTimeoutMinutes: number
    maxLoginAttempts: number
    twoFactorEnabled: boolean
    auditLoggingEnabled: boolean
  }
  notifications: {
    dataIngestionAlertsEnabled: boolean
    emailDeliveryAlertsEnabled: boolean
    systemHealthAlertsEnabled: boolean
    clientActivityAlertsEnabled: boolean
    alertEmailAddress: string
  }
  maintenance: {
    nextScheduledMaintenance: string
    estimatedDowntime: string
  }
}

// New interface for Scraping Source
export interface ScrapingSource {
  id: string
  name: string
  endpoint: string
  last_ingestion: string
  status: "active" | "inactive" | "error"
  records_today: number
  total_records: number
  frequency: "hourly" | "daily" | "weekly" | "monthly"
}

export interface FormState {
  error?: string
  success?: string
  fields?: {
    id?: string // Added for editing existing entities
    email?: string
    firstName?: string
    lastName?: string
    name?: string // For clients/automation classes
    company?: string // For clients
    phone?: string // For clients
    city?: string // New field for clients
    zip_code?: string // New field for clients
    status?: "active" | "inactive" | "pending" // For clients/users/automation classes
    role?: "admin" | "user" // For users
    description?: string // For automation classes
    filters?: string // Stringified JSON for automation classes
    distribution_rules?: string // Stringified JSON for automation classes
    exclusion_rules?: string // Stringified JSON for automation classes
    email_template?: string // Stringified JSON for automation classes
    client_id?: string // For automation classes
    // New fields for SystemConfiguration
    austinApiEndpoint?: string
    ingestionFrequency?: "hourly" | "daily" | "weekly"
    autoIngestionEnabled?: boolean
    dataValidationEnabled?: boolean
    smtpServer?: string
    smtpPort?: string
    fromEmail?: string
    dailySendTime?: string
    emailNotificationsEnabled?: boolean
    sessionTimeoutMinutes?: number
    maxLoginAttempts?: number
    twoFactorEnabled?: boolean
    auditLoggingEnabled?: boolean
    dataIngestionAlertsEnabled?: boolean
    emailDeliveryAlertsEnabled?: boolean
    systemHealthAlertsEnabled?: boolean
    clientActivityAlertsEnabled?: boolean
    alertEmailAddress?: string
  }
}
