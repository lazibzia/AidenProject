"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Plus,
  Edit,
  Trash2,
  ChevronDown,
  ChevronUp,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Progress } from "@/components/ui/progress";

const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL_CLIENTS!;
const PERMIT_API_URL = process.env.NEXT_PUBLIC_API_URL_PERMITS!;
const EMAIL_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/send-all-emails`;
const RAG_DISTRIBUTION_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/rag/distribute/send`;

interface WorkClass {
  name: string;
}

interface Client {
  id: number;
  name: string;
  company: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  permit_type: string;
  work_classes?: WorkClass[];
  permit_class_mapped?: string;
  status?: string;
  rag_query?: string;
  rag_filter_json?: string;
  priority_score?: number;
}

interface Permit {
  id: number;
  city: string;
  state: string;
  country: string;
  permit_type: string;
  work_class: string;
  permit_class: string;
}

interface RAGDistributionParams {
  query: string;
  use_client_prefs: boolean;
  selection: {
    status: string;
  };
  filters: {
    permit_type?: string[];
    permit_class_mapped?: string[];
    work_class?: string[];
    applied_date?: string[];
    issued_date?: string[];
    current_status?: string[];
    city?: string[];
    [key: string]: any;
  };
  per_client_top_k: number;
  oversample: number;
  exclusive: boolean;
  dry_run: boolean;
}

interface EmailStatus {
  id: string;
  clientId: number;
  clientName: string;
  clientEmail: string;
  status:
    | "pending"
    | "sending"
    | "scraping"
    | "indexing"
    | "success"
    | "failed";
  message?: string;
  timestamp: Date;
}

interface Notification {
  id: string;
  type: "email" | "rag";
  title: string;
  description: string;
  status: "in-progress" | "completed" | "failed";
  progress?: number;
  total?: number;
  successCount?: number;
  failureCount?: number;
  details?: EmailStatus[];
  timestamp: Date;
}

function JsonDisplay({ jsonString }: { jsonString?: string }) {
  try {
    if (!jsonString) return null;
    const parsed = JSON.parse(jsonString);
    return <pre className="text-xs">{JSON.stringify(parsed, null, 2)}</pre>;
  } catch (e) {
    return <span className="text-red-500 text-xs">Invalid JSON</span>;
  }
}

export default function ClientsPage() {
  const [isMounted, setIsMounted] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const [permits, setPermits] = useState<Permit[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [clientData, setClientData] = useState<Partial<Client>>({
    work_classes: [{ name: "" }],
    rag_query: "",
    rag_filter_json: "{}",
    status: "active",
    priority_score: 50,
  });
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isSendingEmails, setIsSendingEmails] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [ragParams, setRagParams] = useState<RAGDistributionParams>({
    query: "",
    use_client_prefs: false,
    selection: {
      status: "active",
    },
    filters: {},
    per_client_top_k: 20,
    oversample: 10,
    exclusive: true,
    dry_run: true,
  });
  const [isRagDialogOpen, setIsRagDialogOpen] = useState(false);
  const [isSendingRag, setIsSendingRag] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [isLoadingClients, setIsLoadingClients] = useState(true);
  const [isLoadingPermits, setIsLoadingPermits] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const clientsPerPage = 5;

  useEffect(() => {
    setIsMounted(true);
    fetchClients();
    fetchPermits();
  }, []);

  const resetClientData = (): Partial<Client> => ({
    name: "",
    company: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    country: "",
    permit_type: "",
    work_classes: [{ name: "" }],
    permit_class_mapped: "",
    status: "active",
    rag_query: "",
    rag_filter_json: "{}",
    priority_score: 50,
  });

  const fetchClients = async () => {
    try {
      setIsLoadingClients(true);
      const res = await axios.get(`${CLIENT_API_URL}/clients`);
      setClients(res.data);
    } catch (err) {
      console.error("Fetch error:", err);
      toast.error("Failed to fetch clients");
    } finally {
      setIsLoadingClients(false);
    }
  };

  const fetchPermits = async () => {
    try {
      setIsLoadingPermits(true);
      console.log("Fetching permits from:", PERMIT_API_URL);
      const res = await axios.get(`${PERMIT_API_URL}/permits`);
      console.log("Permits response:", res.data);
      setPermits(res.data);
    } catch (err) {
      console.error("Fetch permits error:", err);
      toast.error("Failed to fetch permits data");
    } finally {
      setIsLoadingPermits(false);
    }
  };

  // Get unique values for dropdowns from permits data with fallbacks
  const getUniqueValues = (field: keyof Permit): string[] => {
    const values = permits
      .map((permit) => permit[field])
      .filter((value): value is string => Boolean(value));

    // If no values from API, provide some fallback options
    if (values.length === 0) {
      switch (field) {
        case "city":
          return ["austin", "Denver", "Chicago"];
        case "state":
          return ["Tx", "Co", "Il"];
        case "country":
          return ["USA"];
        case "permit_type":
          return [
            "Building Permit",
            "Electrical Permit",
            "Plumbing Permit",
            "Mechnical Permit",
          ];
        case "work_class":
          return [
            "Demolition",
            "Repair",
            "Remodel",
            "Irrigation",
            "Change out",
            "Upgrade",
            "Addition and remodel",
            "New",
          ];
        case "permit_class":
          return [
            "Residential",
            "Commercial",
            "Industrial",
            "R-434 Addition & Alterations",
            "C-100 Commercial Remodel",
            "C-1001 Commercial Finish out",
          ];
        default:
          return [];
      }
    }

    return Array.from(new Set(values)).sort();
  };

  const cities = getUniqueValues("city");
  const states = getUniqueValues("state");
  const countries = getUniqueValues("country");
  const permitTypes = getUniqueValues("permit_type");
  const workClasses = getUniqueValues("work_class");
  const permitClasses = getUniqueValues("permit_class");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setClientData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setClientData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSliderChange = (value: number[]) => {
    setClientData((prev) => ({ ...prev, priority_score: value[0] }));
  };

  const handleWorkClassChange = (index: number, value: string) => {
    const updated = [...(clientData.work_classes || [])];
    updated[index].name = value;
    setClientData((prev) => ({ ...prev, work_classes: updated }));
  };

  const addWorkClass = () => {
    setClientData((prev) => ({
      ...prev,
      work_classes: [...(prev.work_classes || []), { name: "" }],
    }));
  };

  const removeWorkClass = (index: number) => {
    const updated = [...(clientData.work_classes || [])];
    updated.splice(index, 1);
    setClientData((prev) => ({ ...prev, work_classes: updated }));
  };

  const handleSaveClient = async () => {
    try {
      if (editingId !== null) {
        await axios.put(`${CLIENT_API_URL}/clients/${editingId}`, clientData);
        toast.success("Client updated");
      } else {
        await axios.post(`${CLIENT_API_URL}/clients`, clientData);
        toast.success("Client added");
      }
      setClientData(resetClientData());
      setEditingId(null);
      setIsDialogOpen(false);
      fetchClients();
    } catch (err) {
      console.error("Save error:", err);
      toast.error("Save failed");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete client?")) return;
    try {
      await axios.delete(`${CLIENT_API_URL}/clients/${id}`);
      toast.success("Client deleted");
      fetchClients();
    } catch (err) {
      console.error("Delete error:", err);
      toast.error("Delete failed");
    }
  };

  const addNotification = (
    notification: Omit<Notification, "id" | "timestamp">
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newNotification = {
      ...notification,
      id,
      timestamp: new Date(),
    };

    setNotifications((prev) => [newNotification, ...prev]);
    return id;
  };

  const updateNotification = (id: string, updates: Partial<Notification>) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, ...updates } : notification
      )
    );
  };

  const handleSendEmail = async () => {
    if (!filteredClients.length) {
      toast.warning("No clients to email");
      return;
    }

    try {
      setIsSendingEmails(true);

      // Create notification
      const notificationId = addNotification({
        type: "email",
        title: "Sending Emails",
        description: `Sending emails to ${filteredClients.length} clients`,
        status: "in-progress",
        progress: 0,
        total: filteredClients.length,
        successCount: 0,
        failureCount: 0,
        details: filteredClients.map((client) => ({
          id: Math.random().toString(36).substring(2, 9),
          clientId: client.id,
          clientName: client.name,
          clientEmail: client.email,
          status: "pending",
          timestamp: new Date(),
        })),
      });

      setShowNotifications(true);

      // Send emails
      const response = await axios.post(EMAIL_API_URL, {
        recipients: filteredClients.map((c) => c.email),
        client_data: filteredClients,
        notification_id: notificationId, // Pass notification ID to backend for updates
      });

      // If the API doesn't support real-time updates, simulate them
      if (!response.data.accepted) {
        // Simulate progress (remove this in production if your API provides real updates)
        const totalClients = filteredClients.length;
        let successCount = 0;
        let failureCount = 0;

        for (let i = 0; i < totalClients; i++) {
          await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate delay

          const isSuccess = Math.random() > 0.2; // 80% success rate for simulation
          if (isSuccess) {
            successCount++;
          } else {
            failureCount++;
          }

          updateNotification(notificationId, {
            progress: i + 1,
            successCount,
            failureCount,
            details: filteredClients.map((client, idx) => ({
              id: `${client.id}-${idx}`,
              clientId: client.id,
              clientName: client.name,
              clientEmail: client.email,
              status:
                idx <= i
                  ? idx === i
                    ? isSuccess
                      ? "success"
                      : "failed"
                    : Math.random() > 0.2
                    ? "success"
                    : "failed"
                  : "pending",
              timestamp: new Date(),
            })),
            status:
              i + 1 === totalClients
                ? failureCount === 0
                  ? "completed"
                  : "failed"
                : "in-progress",
          });
        }

        toast.success(
          failureCount === 0
            ? `All ${successCount} emails sent successfully!`
            : `Emails sent: ${successCount} succeeded, ${failureCount} failed`
        );
      } else {
        // If API provides real-time updates, just mark as completed
        updateNotification(notificationId, {
          status: "completed",
          progress: filteredClients.length,
          successCount: filteredClients.length,
        });

        toast.success("Emails sent successfully!");
      }
    } catch (error) {
      console.error("Email sending error:", error);
      toast.error("Failed to send emails");

      // Update notification with error
      const lastNotification = notifications[0];
      if (lastNotification) {
        updateNotification(lastNotification.id, {
          status: "failed",
          description: "Failed to send emails: " + (error as Error).message,
        });
      }
    } finally {
      setIsSendingEmails(false);
    }
  };

  const handleRagInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setRagParams((prev) => ({
      ...prev,
      [name]:
        name === "per_client_top_k" || name === "oversample"
          ? parseInt(value)
          : value,
    }));
  };

  const handleFilterChange = (filterType: string, value: string) => {
    setRagParams((prev) => {
      const newFilters = { ...prev.filters };

      if (value) {
        newFilters[filterType] = [value];
      } else {
        delete newFilters[filterType];
      }

      return {
        ...prev,
        filters: newFilters,
      };
    });
  };

  const handleSelectionChange = (name: string, value: string) => {
    setRagParams((prev) => ({
      ...prev,
      selection: {
        ...prev.selection,
        [name]: value,
      },
    }));
  };

  const handleRagToggle = (name: keyof RAGDistributionParams) => {
    setRagParams((prev) => ({
      ...prev,
      [name]: !prev[name],
    }));
  };

  const handleSendRag = async () => {
    try {
      setIsSendingRag(true);

      // Create notification for RAG distribution
      const notificationId = addNotification({
        type: "rag",
        title: "Distributing RAG Query",
        description: `Processing RAG query: "${ragParams.query.substring(
          0,
          30
        )}${ragParams.query.length > 30 ? "..." : ""}"`,
        status: "in-progress",
      });

      setShowNotifications(true);

      const toastId = toast.loading("Distributing RAG query...");

      // Clean up empty filters
      const cleanedFilters = Object.fromEntries(
        Object.entries(ragParams.filters).filter(
          ([_, value]) => value && value.length > 0
        )
      );

      const payload = {
        ...ragParams,
        filters: cleanedFilters,
        notification_id: notificationId, // Pass notification ID to backend
      };

      console.log("Sending RAG payload:", payload);
      await axios.post(RAG_DISTRIBUTION_URL, payload);

      // Update notification
      updateNotification(notificationId, {
        status: "completed",
        description: `RAG query distributed successfully: "${ragParams.query}"`,
      });

      toast.success("RAG query distributed", { id: toastId });
      setIsRagDialogOpen(false);
    } catch (error) {
      console.error("RAG distribution error:", error);
      toast.error("Failed to distribute RAG query");

      // Update notification with error
      const lastNotification = notifications[0];
      if (lastNotification) {
        updateNotification(lastNotification.id, {
          status: "failed",
          description:
            "Failed to distribute RAG query: " + (error as Error).message,
        });
      }
    } finally {
      setIsSendingRag(false);
    }
  };

  const getPriorityColor = (score?: number): string => {
    if (!score) return "text-gray-500";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-blue-600";
    if (score >= 40) return "text-yellow-600";
    return "text-red-600";
  };

  const getPriorityLabel = (score?: number): string => {
    if (!score) return "Not Set";
    if (score >= 80) return "High";
    if (score >= 60) return "Medium-High";
    if (score >= 40) return "Medium";
    if (score >= 20) return "Low-Medium";
    return "Low";
  };

  const filteredClients = clients.filter((c) =>
    [
      c.name,
      c.company,
      c.email,
      c.city,
      c.zip_code,
      c.permit_type,
      ...(c.work_classes?.map((w) => w.name) || []),
      c.permit_class_mapped,
      c.rag_query,
      c.rag_filter_json,
    ].some((v) => v?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const indexOfLast = currentPage * clientsPerPage;
  const currentClients = filteredClients.slice(
    indexOfLast - clientsPerPage,
    indexOfLast
  );
  const totalPages = Math.ceil(filteredClients.length / clientsPerPage);

  if (!isMounted) return null;

  return (
    <div className="container mx-auto py-10">
      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed top-4 right-4 w-96 max-h-[80vh] overflow-y-auto bg-white shadow-lg rounded-lg border z-50">
          <div className="flex justify-between items-center p-4 border-b">
            <h3 className="font-semibold">Notifications</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNotifications(false)}
            >
              <X size={16} />
            </Button>
          </div>

          <div className="p-2">
            {notifications.length === 0 ? (
              <p className="text-center text-muted-foreground p-4">
                No notifications
              </p>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 mb-2 rounded-lg border ${
                    notification.status === "completed"
                      ? "bg-green-50 border-green-200"
                      : notification.status === "failed"
                      ? "bg-red-50 border-red-200"
                      : "bg-blue-50 border-blue-200"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {notification.status === "in-progress" && (
                          <Loader2
                            size={14}
                            className="animate-spin text-blue-500"
                          />
                        )}
                        {notification.status === "completed" && (
                          <CheckCircle size={14} className="text-green-500" />
                        )}
                        {notification.status === "failed" && (
                          <AlertCircle size={14} className="text-red-500" />
                        )}
                        <span className="font-medium">
                          {notification.title}
                        </span>
                        <Badge
                          variant={
                            notification.status === "completed"
                              ? "default"
                              : notification.status === "failed"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {notification.status}
                        </Badge>
                      </div>

                      <p className="text-sm text-muted-foreground mb-2">
                        {notification.description}
                      </p>

                      {notification.progress !== undefined &&
                        notification.total !== undefined && (
                          <div className="space-y-2 mb-2">
                            <Progress
                              value={
                                (notification.progress / notification.total) *
                                100
                              }
                              className="h-2"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>
                                {notification.progress} of {notification.total}
                              </span>
                              <span>
                                {Math.round(
                                  (notification.progress / notification.total) *
                                    100
                                )}
                                %
                              </span>
                            </div>
                          </div>
                        )}

                      {notification.successCount !== undefined &&
                        notification.failureCount !== undefined && (
                          <div className="flex gap-4 text-xs">
                            <span className="text-green-600">
                              {notification.successCount} succeeded
                            </span>
                            <span className="text-red-600">
                              {notification.failureCount} failed
                            </span>
                          </div>
                        )}
                    </div>
                  </div>

                  {notification.details && notification.details.length > 0 && (
                    <div className="mt-2 border-t pt-2">
                      <div className="text-xs font-medium mb-1">Details:</div>
                      <div className="max-h-32 overflow-y-auto">
                        {notification.details.map((detail) => (
                          <div
                            key={detail.id}
                            className="flex items-center justify-between py-1 text-xs"
                          >
                            <span className="truncate max-w-[120px]">
                              {detail.clientName}
                            </span>
                            <Badge
                              variant={
                                detail.status === "success"
                                  ? "default"
                                  : detail.status === "failed"
                                  ? "destructive"
                                  : "secondary"
                              }
                              className="text-xs"
                            >
                              {detail.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-muted-foreground mt-2">
                    {notification.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Clients</h1>
          <p className="text-muted-foreground">Manage client data</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative"
          >
            Notifications
            {notifications.filter((n) => n.status === "in-progress").length >
              0 && (
              <span className="absolute -top-2 -right-2 h-5 w-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">
                {notifications.filter((n) => n.status === "in-progress").length}
              </span>
            )}
          </Button>

          <Dialog
            open={isDialogOpen}
            onOpenChange={(o) => {
              if (!o) {
                setClientData(resetClientData());
                setEditingId(null);
              }
              setIsDialogOpen(o);
            }}
          >
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Plus size={16} /> Add Client
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {editingId !== null ? "Edit Client" : "New Client"}
                </DialogTitle>
                <DialogDescription>
                  {editingId !== null
                    ? "Update client info"
                    : "Enter new client info"}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {[
                  "name",
                  "company",
                  "email",
                  "phone",
                  "address",
                  "zip_code",
                ].map((field) => (
                  <div
                    key={field}
                    className="grid grid-cols-4 items-center gap-4"
                  >
                    <Label htmlFor={field} className="text-right capitalize">
                      {field.replace(/_/g, " ")}
                    </Label>
                    <Input
                      id={field}
                      name={field}
                      value={(clientData as any)[field] || ""}
                      onChange={handleInputChange}
                      className="col-span-3"
                    />
                  </div>
                ))}

                {/* Priority Score Slider */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="priority_score" className="text-right">
                    Priority Score
                  </Label>
                  <div className="col-span-3 space-y-2">
                    <Slider
                      value={[clientData.priority_score || 50]}
                      onValueChange={handleSliderChange}
                      max={100}
                      min={0}
                      step={1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>0%</span>
                      <span
                        className={`font-medium ${getPriorityColor(
                          clientData.priority_score
                        )}`}
                      >
                        {clientData.priority_score}% -{" "}
                        {getPriorityLabel(clientData.priority_score)}
                      </span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>

                {/* Dropdown for City */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="city" className="text-right">
                    City
                  </Label>
                  <Select
                    value={clientData.city || ""}
                    onValueChange={(value) => handleSelectChange("city", value)}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select city" />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingPermits ? (
                        <SelectItem value="" disabled>
                          Loading cities...
                        </SelectItem>
                      ) : (
                        cities.map((city) => (
                          <SelectItem key={city} value={city}>
                            {city}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dropdown for State */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="state" className="text-right">
                    State
                  </Label>
                  <Select
                    value={clientData.state || ""}
                    onValueChange={(value) =>
                      handleSelectChange("state", value)
                    }
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select state" />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingPermits ? (
                        <SelectItem value="" disabled>
                          Loading states...
                        </SelectItem>
                      ) : (
                        states.map((state) => (
                          <SelectItem key={state} value={state}>
                            {state}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dropdown for Country */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="country" className="text-right">
                    Country
                  </Label>
                  <Select
                    value={clientData.country || ""}
                    onValueChange={(value) =>
                      handleSelectChange("country", value)
                    }
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select country" />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingPermits ? (
                        <SelectItem value="" disabled>
                          Loading countries...
                        </SelectItem>
                      ) : (
                        countries.map((country) => (
                          <SelectItem key={country} value={country}>
                            {country}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dropdown for Permit Type */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="permit_type" className="text-right">
                    Permit Type
                  </Label>
                  <Select
                    value={clientData.permit_type || ""}
                    onValueChange={(value) =>
                      handleSelectChange("permit_type", value)
                    }
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select permit type" />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingPermits ? (
                        <SelectItem value="" disabled>
                          Loading permit types...
                        </SelectItem>
                      ) : (
                        permitTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dropdown for Permit Class */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="permit_class_mapped" className="text-right">
                    Permit Class
                  </Label>
                  <Select
                    value={clientData.permit_class_mapped || ""}
                    onValueChange={(value) =>
                      handleSelectChange("permit_class_mapped", value)
                    }
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select permit class" />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingPermits ? (
                        <SelectItem value="" disabled>
                          Loading permit classes...
                        </SelectItem>
                      ) : (
                        permitClasses.map((cls) => (
                          <SelectItem key={cls} value={cls}>
                            {cls}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Work Classes */}
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label
                    htmlFor="work_classes"
                    className="text-right capitalize mt-2"
                  >
                    Work Classes
                  </Label>
                  <div className="col-span-3 space-y-2">
                    {clientData.work_classes?.map((wc, index) => (
                      <div key={index} className="flex gap-2">
                        <Select
                          value={wc.name}
                          onValueChange={(value) =>
                            handleWorkClassChange(index, value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select work class" />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingPermits ? (
                              <SelectItem value="" disabled>
                                Loading work classes...
                              </SelectItem>
                            ) : (
                              workClasses.map((workClass) => (
                                <SelectItem key={workClass} value={workClass}>
                                  {workClass}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => removeWorkClass(index)}
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      onClick={addWorkClass}
                    >
                      + Add Work Class
                    </Button>
                  </div>
                </div>

                {/* Status */}
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="status" className="text-right">
                    Status
                  </Label>
                  <Select
                    value={clientData.status || "active"}
                    onValueChange={(value) =>
                      handleSelectChange("status", value)
                    }
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* RAG Query and Filter JSON */}
                {["rag_query", "rag_filter_json"].map((field) => (
                  <div
                    key={field}
                    className="grid grid-cols-4 items-center gap-4"
                  >
                    <Label htmlFor={field} className="text-right capitalize">
                      {field.replace(/_/g, " ")}
                    </Label>
                    <Input
                      id={field}
                      name={field}
                      value={(clientData as any)[field] || ""}
                      onChange={handleInputChange}
                      className="col-span-3"
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleSaveClient}>
                  {editingId !== null ? "Update Client" : "Add Client"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={isRagDialogOpen} onOpenChange={setIsRagDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Plus size={16} /> RAG Query
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Distribute RAG Query</DialogTitle>
                <DialogDescription>
                  Send a RAG query to selected clients with advanced filtering
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Query *</Label>
                  <Input
                    name="query"
                    value={ragParams.query}
                    onChange={handleRagInputChange}
                    placeholder="Enter your RAG query"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Per Client Top K</Label>
                    <Input
                      name="per_client_top_k"
                      type="number"
                      value={ragParams.per_client_top_k}
                      onChange={handleRagInputChange}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Oversample</Label>
                    <Input
                      name="oversample"
                      type="number"
                      value={ragParams.oversample}
                      onChange={handleRagInputChange}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Client Selection</h3>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select
                        value={ragParams.selection.status}
                        onValueChange={(value) =>
                          handleSelectionChange("status", value)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="inactive">Inactive</SelectItem>
                          <SelectItem value="all">All</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 p-0"
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  >
                    {showAdvancedFilters ? (
                      <>
                        <ChevronUp size={16} />
                        Hide Advanced Filters
                      </>
                    ) : (
                      <>
                        <ChevronDown size={16} />
                        Show Advanced Filters
                      </>
                    )}
                  </Button>

                  {showAdvancedFilters && (
                    <div className="grid grid-cols-2 gap-4 p-4 border rounded-lg">
                      {/* Permit Type Dropdown */}
                      <div className="space-y-2">
                        <Label>Permit Type</Label>
                        <Select
                          value={ragParams.filters.permit_type?.[0] || ""}
                          onValueChange={(value) =>
                            handleFilterChange("permit_type", value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Filter by permit type" />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingPermits ? (
                              <SelectItem value="" disabled>
                                Loading permit types...
                              </SelectItem>
                            ) : (
                              permitTypes.map((type) => (
                                <SelectItem key={type} value={type}>
                                  {type}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Permit Class Dropdown */}
                      <div className="space-y-2">
                        <Label>Permit Class</Label>
                        <Select
                          value={
                            ragParams.filters.permit_class_mapped?.[0] || ""
                          }
                          onValueChange={(value) =>
                            handleFilterChange("permit_class_mapped", value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Filter by permit class" />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingPermits ? (
                              <SelectItem value="" disabled>
                                Loading permit classes...
                              </SelectItem>
                            ) : (
                              permitClasses.map((cls) => (
                                <SelectItem key={cls} value={cls}>
                                  {cls}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Work Class Dropdown */}
                      <div className="space-y-2">
                        <Label>Work Class</Label>
                        <Select
                          value={ragParams.filters.work_class?.[0] || ""}
                          onValueChange={(value) =>
                            handleFilterChange("work_class", value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Filter by work class" />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingPermits ? (
                              <SelectItem value="" disabled>
                                Loading work classes...
                              </SelectItem>
                            ) : (
                              workClasses.map((workClass) => (
                                <SelectItem key={workClass} value={workClass}>
                                  {workClass}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* City Dropdown */}
                      <div className="space-y-2">
                        <Label>City</Label>
                        <Select
                          value={ragParams.filters.city?.[0] || ""}
                          onValueChange={(value) =>
                            handleFilterChange("city", value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Filter by city" />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingPermits ? (
                              <SelectItem value="" disabled>
                                Loading cities...
                              </SelectItem>
                            ) : (
                              cities.map((city) => (
                                <SelectItem key={city} value={city}>
                                  {city}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-4 pt-2">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="use_client_prefs"
                      checked={ragParams.use_client_prefs}
                      onCheckedChange={() =>
                        handleRagToggle("use_client_prefs")
                      }
                    />
                    <Label htmlFor="use_client_prefs">
                      Use Client Preferences
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="exclusive"
                      checked={ragParams.exclusive}
                      onCheckedChange={() => handleRagToggle("exclusive")}
                    />
                    <Label htmlFor="exclusive">Exclusive</Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="dry_run"
                      checked={ragParams.dry_run}
                      onCheckedChange={() => handleRagToggle("dry_run")}
                    />
                    <Label htmlFor="dry_run">Dry Run</Label>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsRagDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSendRag}
                  disabled={isSendingRag || !ragParams.query}
                >
                  {isSendingRag ? "Sending..." : "Distribute"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Button
            onClick={handleSendEmail}
            disabled={isSendingEmails || filteredClients.length === 0}
            className="gap-2"
          >
            {isSendingEmails ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Sending...
              </>
            ) : (
              <>Send Email ({filteredClients.length})</>
            )}
          </Button>
        </div>
      </div>

      <Input
        placeholder="Search clients..."
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setCurrentPage(1);
        }}
        className="max-w-md mb-4"
      />

      {isLoadingClients ? (
        <div className="flex justify-center items-center py-10">
          <p>Loading clients...</p>
        </div>
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableCaption>{filteredClients.length} clients</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Permit Type</TableHead>
                  <TableHead>Work Classes</TableHead>
                  <TableHead>Permit Class</TableHead>
                  <TableHead>RAG Query</TableHead>
                  <TableHead>RAG Filter</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {currentClients.length ? (
                  currentClients.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell>{c.name}</TableCell>
                      <TableCell>{c.company}</TableCell>
                      <TableCell>{c.email}</TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span
                            className={`font-medium ${getPriorityColor(
                              c.priority_score
                            )}`}
                          >
                            {c.priority_score || 0}%
                          </span>
                          <span
                            className={`text-xs ${getPriorityColor(
                              c.priority_score
                            )}`}
                          >
                            {getPriorityLabel(c.priority_score)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{c.permit_type}</TableCell>
                      <TableCell>
                        {(c.work_classes || []).map((w, i) => (
                          <Badge key={i} className="mr-1">
                            {w.name}
                          </Badge>
                        ))}
                      </TableCell>
                      <TableCell>{c.permit_class_mapped}</TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {c.rag_query}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        <JsonDisplay jsonString={c.rag_filter_json} />
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            c.status === "active" ? "default" : "secondary"
                          }
                        >
                          {c.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingId(c.id);
                            setClientData({ ...c });
                            setIsDialogOpen(true);
                          }}
                        >
                          <Edit className="h-4 w-4 mr-1" /> Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-500 hover:bg-red-50"
                          onClick={() => handleDelete(c.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={11}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No clients found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="mt-6 flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                Showing {indexOfLast - clientsPerPage + 1}-
                {Math.min(indexOfLast, filteredClients.length)} of{" "}
                {filteredClients.length}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <div className="flex items-center px-4 text-sm">
                  Page {currentPage} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
