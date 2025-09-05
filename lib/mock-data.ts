import type {
  Permit,
  Client,
  AutomationClass,
  SystemStats,
  AdminUser,
  SystemConfiguration,
  ScrapingSource,
} from "./types"

export const mockPermits: Permit[] = [
  {
    id: "1",
    permit_type_desc: "Commercial Building Permit",
    applied_date: "2024-12-20",
    issue_date: "2024-12-21",
    address: "123 Main St, Austin, TX",
    zip_code: "78701",
    council_district: "District 9",
    contractor_name: "ABC Construction",
    contractor_category: "General Contractor",
    contractor_phone: "(512) 555-0123",
    work_class_group: "Commercial",
    project_description: "New office building construction",
    valuation: 2500000,
    square_footage: 15000,
    status: "active",
  },
  {
    id: "2",
    permit_type_desc: "Demolition Permit",
    applied_date: "2024-12-19",
    issue_date: "2024-12-21",
    address: "456 Oak Ave, Austin, TX",
    zip_code: "78702",
    council_district: "District 3",
    contractor_name: "Demo Pro Services",
    contractor_category: "Demolition",
    contractor_phone: "(512) 555-0456",
    work_class_group: "Demolition",
    project_description: "Residential home demolition",
    valuation: 25000,
    square_footage: 2500,
    status: "active",
  },
  {
    id: "3",
    permit_type_desc: "Residential Addition",
    applied_date: "2024-12-18",
    issue_date: "2024-12-21",
    address: "789 Pine St, Austin, TX",
    zip_code: "78703",
    council_district: "District 5",
    contractor_name: "Home Builders LLC",
    contractor_category: "Residential",
    contractor_phone: "(512) 555-0789",
    work_class_group: "Residential",
    project_description: "Kitchen and bathroom addition",
    valuation: 150000,
    square_footage: 800,
    status: "active",
  },
]

export const mockClients: Client[] = [
  {
    id: "1",
    name: "John Smith",
    email: "john@wastemanagement.com",
    company: "Austin Waste Management",
    phone: "(512) 555-1000",
    city: "Austin", // Added city
    zip_code: "78701", // Added zip_code
    created_date: "2024-11-15",
    status: "active",
    automation_classes: [],
  },
  {
    id: "2",
    name: "Sarah Johnson",
    email: "sarah@demolitionpro.com",
    company: "Demolition Pro Services",
    phone: "(512) 555-2000",
    city: "Houston", // Added city
    zip_code: "77002", // Added zip_code
    created_date: "2024-11-20",
    status: "active",
    automation_classes: [],
  },
  {
    id: "3",
    name: "Mike Wilson",
    email: "mike@contractorservices.com",
    company: "Wilson Contracting",
    phone: "(512) 555-3000",
    city: "Dallas", // Added city
    zip_code: "75201", // Added zip_code
    created_date: "2024-12-01",
    status: "inactive",
    automation_classes: [],
  },
]

export function addMockClient(newClientData: Omit<Client, "id" | "created_date" | "automation_classes">): Client {
  const newClient: Client = {
    id: Date.now().toString(), // Simple unique ID
    created_date: new Date().toISOString().split("T")[0],
    automation_classes: [],
    ...newClientData,
  }
  mockClients.push(newClient)
  return newClient
}

export function updateMockClient(clientId: string, updatedData: Partial<Client>): Client | null {
  const clientIndex = mockClients.findIndex((c) => c.id === clientId)
  if (clientIndex > -1) {
    mockClients[clientIndex] = { ...mockClients[clientIndex], ...updatedData }
    return mockClients[clientIndex]
  }
  return null
}

export function deleteMockClient(clientId: string): boolean {
  const initialLength = mockClients.length
  const updatedClients = mockClients.filter((c) => c.id !== clientId)
  // To actually modify the original array, we need to reassign it or use splice
  mockClients.length = 0 // Clear existing array
  mockClients.push(...updatedClients) // Push filtered items back
  return mockClients.length < initialLength
}

export const mockAutomationClasses: AutomationClass[] = [
  {
    id: "1",
    client_id: "1",
    name: "Commercial Demolition Leads",
    description: "Demolition permits for commercial properties over $50k",
    filters: [
      { field: "permit_type_desc", operator: "contains", value: "Demolition" },
      { field: "work_class_group", operator: "equals", value: "Commercial" },
      { field: "valuation", operator: "greater_than", value: "50000" },
    ],
    distribution_rules: {
      type: "territory",
      config: { territories: ["78701", "78702", "78703"] },
    },
    exclusion_rules: [{ field: "contractor_name", operator: "contains", value: "Competitor ABC" }],
    email_template: {
      subject: "Daily Commercial Demolition Leads - {{date}}",
      body: "Here are your daily demolition leads for Austin commercial properties.",
      format: "xlsx",
    },
    status: "active",
    created_date: "2024-11-15",
    last_run: "2024-12-21",
    leads_sent_today: 3,
  },
  {
    id: "2",
    client_id: "2",
    name: "Residential Construction",
    description: "New residential construction and additions",
    filters: [
      { field: "work_class_group", operator: "equals", value: "Residential" },
      { field: "permit_type_desc", operator: "contains", value: "Addition" },
    ],
    distribution_rules: {
      type: "round_robin",
      config: { priority: 1 },
    },
    exclusion_rules: [],
    email_template: {
      subject: "Residential Construction Leads - {{date}}",
      body: "Your daily residential construction leads are attached.",
      format: "csv",
    },
    status: "active",
    created_date: "2024-11-20",
    last_run: "2024-12-21",
    leads_sent_today: 5,
  },
]

export function addMockAutomationClass(
  newClassData: Omit<AutomationClass, "id" | "created_date" | "last_run" | "leads_sent_today">,
): AutomationClass {
  const newClass: AutomationClass = {
    id: Date.now().toString(),
    created_date: new Date().toISOString().split("T")[0],
    last_run: "Never",
    leads_sent_today: 0,
    ...newClassData,
  }
  mockAutomationClasses.push(newClass)
  return newClass
}

export function updateMockAutomationClass(
  classId: string,
  updatedData: Partial<AutomationClass>,
): AutomationClass | null {
  const classIndex = mockAutomationClasses.findIndex((ac) => ac.id === classId)
  if (classIndex > -1) {
    mockAutomationClasses[classIndex] = { ...mockAutomationClasses[classIndex], ...updatedData }
    return mockAutomationClasses[classIndex]
  }
  return null
}

export function deleteMockAutomationClass(classId: string): boolean {
  const initialLength = mockAutomationClasses.length
  const updatedClasses = mockAutomationClasses.filter((ac) => ac.id !== classId)
  mockAutomationClasses.length = 0
  mockAutomationClasses.push(...updatedClasses)
  return mockAutomationClasses.length < initialLength
}

export function toggleMockAutomationClassStatus(
  classId: string,
  newStatus: "active" | "inactive",
): AutomationClass | null {
  const classIndex = mockAutomationClasses.findIndex((ac) => ac.id === classId)
  if (classIndex > -1) {
    mockAutomationClasses[classIndex].status = newStatus
    return mockAutomationClasses[classIndex]
  }
  return null
}

export const mockSystemStats: SystemStats = {
  total_permits: 15847,
  permits_today: 23,
  active_clients: 12,
  automation_classes: 8,
  emails_sent_today: 156,
  system_uptime: "99.9%",
}

// New async function to get mock system stats with a very small delay
export async function getMockSystemStats(): Promise<SystemStats> {
  await new Promise((resolve) => setTimeout(resolve, 50)) // Reduced delay
  return mockSystemStats
}

// New async function to get mock clients with a very small delay
export async function getMockClients(): Promise<Client[]> {
  await new Promise((resolve) => setTimeout(resolve, 70)) // Reduced delay
  return mockClients
}

export const mockAdminUsers: (AdminUser & { password: string })[] = [
  {
    id: "1",
    email: "admin@permitplatform.com",
    firstName: "System",
    lastName: "Administrator",
    role: "admin",
    status: "active",
    created_date: "2024-01-15",
    last_login: "2024-12-21",
    password: "admin123",
    permissions: [
      { module: "permits", actions: ["read", "write", "delete", "admin"] },
      { module: "clients", actions: ["read", "write", "delete", "admin"] },
      { module: "automation", actions: ["read", "write", "delete", "admin"] },
      { module: "analytics", actions: ["read", "write", "delete", "admin"] },
      { module: "settings", actions: ["read", "write", "delete", "admin"] },
      { module: "data-sources", actions: ["read", "write", "delete", "admin"] },
    ],
  },
  {
    id: "2",
    email: "john.user@permitplatform.com",
    firstName: "John",
    lastName: "User",
    role: "user",
    status: "active",
    created_date: "2024-02-20",
    last_login: "2024-12-20",
    password: "user123",
    permissions: [
      { module: "permits", actions: ["read"] },
      { module: "clients", actions: ["read", "write"] },
      { module: "automation", actions: ["read"] },
      { module: "analytics", actions: ["read"] },
      { module: "data-sources", actions: ["read"] },
    ],
  },
  {
    id: "3",
    email: "sarah.user@permitplatform.com",
    firstName: "Sarah",
    lastName: "User",
    role: "user",
    status: "pending",
    created_date: "2024-03-10",
    last_login: "",
    password: "user123",
    permissions: [
      { module: "permits", actions: ["read"] },
      { module: "clients", actions: ["read", "write"] },
      { module: "automation", actions: ["read"] },
      { module: "analytics", actions: ["read"] },
    ],
  },
]

// New mock data for System Configuration
export const mockSystemConfiguration: SystemConfiguration = {
  dataSource: {
    austinApiEndpoint: "https://data.austintexas.gov/resource/3syk-w9eu.json",
    ingestionFrequency: "monthly", // Changed default to monthly
    autoIngestionEnabled: true,
    dataValidationEnabled: true,
  },
  email: {
    smtpServer: "smtp.sendgrid.net",
    smtpPort: "587",
    fromEmail: "leads@permitplatform.com",
    dailySendTime: "08:00",
    emailNotificationsEnabled: true,
  },
  security: {
    sessionTimeoutMinutes: 480,
    maxLoginAttempts: 5,
    twoFactorEnabled: false,
    auditLoggingEnabled: true,
  },
  notifications: {
    dataIngestionAlertsEnabled: true,
    emailDeliveryAlertsEnabled: true,
    systemHealthAlertsEnabled: true,
    clientActivityAlertsEnabled: false,
    alertEmailAddress: "admin@permitplatform.com",
  },
  maintenance: {
    nextScheduledMaintenance: "Sunday, December 29, 2024 at 2:00 AM CST",
    estimatedDowntime: "30 minutes",
  },
}

// Function to update system configuration
export function updateMockSystemConfiguration(
  section: keyof SystemConfiguration,
  updatedData: Partial<SystemConfiguration[typeof section]>,
): SystemConfiguration {
  mockSystemConfiguration[section] = {
    ...mockSystemConfiguration[section],
    ...updatedData,
  }
  return mockSystemConfiguration
}

export const mockScrapingSources: ScrapingSource[] = [
  {
    id: "src-austin-permits",
    name: "Austin, TX Building Permits",
    endpoint: "https://data.austintexas.gov/resource/3syk-w9eu.json",
    last_ingestion: "2024-12-21 08:00 AM",
    status: "active",
    records_today: 23,
    total_records: 15847,
    frequency: "daily",
  },
  {
    id: "src-houston-licenses",
    name: "Houston, TX Business Licenses",
    endpoint: "https://data.houstontx.gov/resource/r34t-234x.json",
    last_ingestion: "2024-12-20 10:30 PM",
    status: "active",
    records_today: 15,
    total_records: 8921,
    frequency: "daily",
  },
  {
    id: "src-dallas-inspections",
    name: "Dallas, TX Inspection Records",
    endpoint: "https://data.dallascityhall.com/resource/d4s5-e6f7.json",
    last_ingestion: "2024-12-21 01:00 AM",
    status: "active",
    records_today: 5,
    total_records: 23456,
    frequency: "hourly",
  },
  {
    id: "src-sanantonio-zoning",
    name: "San Antonio, TX Zoning Cases",
    endpoint: "https://data.sanantonio.gov/resource/s7d8-f9g0.json",
    last_ingestion: "2024-12-19 09:00 AM",
    status: "inactive",
    records_today: 0,
    total_records: 1234,
    frequency: "weekly",
  },
  {
    id: "src-elpaso-violations",
    name: "El Paso, TX Code Violations",
    endpoint: "https://data.elpasotexas.gov/resource/e1r2-t3y4.json",
    last_ingestion: "2024-12-21 07:00 AM",
    status: "error",
    records_today: 0,
    total_records: 5678,
    frequency: "daily",
  },
  {
    id: "src-fortworth-permits",
    name: "Fort Worth, TX Building Permits",
    endpoint: "https://data.fortworthtexas.gov/resource/f5g6-h7j8.json",
    last_ingestion: "2024-12-21 09:00 AM",
    status: "active",
    records_today: 18,
    total_records: 11223,
    frequency: "daily",
  },
  {
    id: "src-plano-development",
    name: "Plano, TX Development Projects",
    endpoint: "https://data.plano.gov/resource/p9q0-r1s2.json",
    last_ingestion: "2024-12-20 04:00 PM",
    status: "active",
    records_today: 7,
    total_records: 987,
    frequency: "weekly",
  },
  {
    id: "src-corpuschristi-permits",
    name: "Corpus Christi, TX Permits",
    endpoint: "https://data.cctexas.com/resource/c3v4-b5n6.json",
    last_ingestion: "2024-12-21 06:00 AM",
    status: "active",
    records_today: 10,
    total_records: 4567,
    frequency: "daily",
  },
  {
    id: "src-laredo-inspections",
    name: "Laredo, TX Inspections",
    endpoint: "https://data.ci.laredo.tx.us/resource/l7k8-j9h0.json",
    last_ingestion: "2024-12-20 11:00 AM",
    status: "inactive",
    records_today: 0,
    total_records: 2109,
    frequency: "monthly",
  },
  {
    id: "src-lubbock-permits",
    name: "Lubbock, TX Permits",
    endpoint: "https://data.mylubbock.us/resource/lb12-cd34.json",
    last_ingestion: "2024-12-21 05:00 AM",
    status: "active",
    records_today: 12,
    total_records: 7890,
    frequency: "daily",
  },
  {
    id: "src-garland-licenses",
    name: "Garland, TX Business Licenses",
    endpoint: "https://data.garlandtx.gov/resource/g5f6-e7d8.json",
    last_ingestion: "2024-12-20 02:00 PM",
    status: "active",
    records_today: 9,
    total_records: 3210,
    frequency: "weekly",
  },
  {
    id: "src-irving-permits",
    name: "Irving, TX Building Permits",
    endpoint: "https://data.cityofirving.org/resource/i9j0-k1l2.json",
    last_ingestion: "2024-12-21 07:30 AM",
    status: "active",
    records_today: 14,
    total_records: 6543,
    frequency: "daily",
  },
]
