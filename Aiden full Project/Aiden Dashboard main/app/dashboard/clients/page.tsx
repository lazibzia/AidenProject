"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Plus, Edit, Trash2 } from "lucide-react";
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
import { toast } from "sonner";

const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL_CLIENTS!;
const EMAIL_API_URL = "http://127.0.0.1:5003/api/send-all-emails"; // Fixed typo in endpoint

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
  status?: string;
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [newClient, setNewClient] = useState<Omit<Client, "id">>(
    initialClientState()
  );
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [isSendingEmails, setIsSendingEmails] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const clientsPerPage = 5;

  function initialClientState(): Omit<Client, "id"> {
    return {
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
      status: "active",
    };
  }

  const fetchClients = async () => {
    try {
      const res = await axios.get(`${CLIENT_API_URL}/clients`);
      setClients(res.data);
    } catch (err) {
      console.error("Failed to fetch clients:", err);
      toast.error("Failed to fetch clients");
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    field: keyof Omit<Client, "id">
  ) => {
    const value = e.target.value;
    if (editingClient) {
      setEditingClient({ ...editingClient, [field]: value });
    } else {
      setNewClient({ ...newClient, [field]: value });
    }
  };

  const handleAddOrUpdateClient = async () => {
    try {
      if (editingClient) {
        await axios.put(
          `${CLIENT_API_URL}/clients/${editingClient.id}`,
          editingClient
        );
        toast.success("Client updated successfully");
      } else {
        await axios.post(`${CLIENT_API_URL}/clients`, newClient);
        toast.success("Client added successfully");
      }
      setNewClient(initialClientState());
      setEditingClient(null);
      setIsDialogOpen(false);
      fetchClients();
    } catch (err) {
      console.error("Failed to save client:", err);
      toast.error("Failed to save client");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`${CLIENT_API_URL}/clients/${id}`);
      toast.success("Client deleted successfully");
      fetchClients();
    } catch (err) {
      console.error("Failed to delete client:", err);
      toast.error("Failed to delete client");
    }
  };

  const handleSendEmailToAll = async () => {
    if (filteredClients.length === 0) {
      toast.warning("No clients available to send emails");
      return;
    }

    try {
      setIsSendingEmails(true);
      const toastId = toast.loading(
        `Sending emails to ${filteredClients.length} clients...`
      );

      // Debug: Log what we're sending
      console.log("Sending to endpoint:", EMAIL_API_URL);
      console.log("Sending data:", {
        recipients: filteredClients.map((c) => c.email),
        client_data: filteredClients,
      });

      const response = await axios.post(
        EMAIL_API_URL,
        {
          recipients: filteredClients.map((c) => c.email),
          client_data: filteredClients,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Email API response:", response);

      if (response.status === 200) {
        toast.success(`Emails sent successfully!`, { id: toastId });
      } else {
        toast.error("Emails were not sent successfully", { id: toastId });
      }
    } catch (err: any) {
      console.error("Email sending error:", err);
      let errorMessage = "Failed to send emails";

      if (err.response) {
        console.error("Response data:", err.response.data);
        console.error("Response status:", err.response.status);
        errorMessage = err.response.data.message || errorMessage;
      } else if (err.request) {
        console.error("No response received:", err.request);
        errorMessage = "No response from server";
      }

      toast.error(errorMessage);
    } finally {
      setIsSendingEmails(false);
    }
  };

  const filteredClients = clients.filter((client) =>
    [
      client.name,
      client.company,
      client.email,
      client.city,
      client.zip_code,
      client.permit_type,
    ].some((field) => field?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const indexOfLast = currentPage * clientsPerPage;
  const indexOfFirst = indexOfLast - clientsPerPage;
  const currentClients = filteredClients.slice(indexOfFirst, indexOfLast);
  const totalPages = Math.ceil(filteredClients.length / clientsPerPage);

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Client Management</h1>
          <p className="text-muted-foreground">Manage your client database</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Plus size={16} /> Add Client
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>
                  {editingClient ? "Edit Client" : "Create New Client"}
                </DialogTitle>
                <DialogDescription>
                  {editingClient
                    ? "Update the client information below"
                    : "Fill in the details for a new client"}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {Object.keys(initialClientState()).map((field) => (
                  <div
                    key={field}
                    className="grid grid-cols-4 items-center gap-4"
                  >
                    <Label htmlFor={field} className="text-right capitalize">
                      {field.replace("_", " ")}
                    </Label>
                    <Input
                      id={field}
                      value={
                        editingClient
                          ? editingClient[field as keyof Client] || ""
                          : newClient[field as keyof Omit<Client, "id">] || ""
                      }
                      onChange={(e) =>
                        handleChange(e, field as keyof Omit<Client, "id">)
                      }
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
                <Button onClick={handleAddOrUpdateClient}>
                  {editingClient ? "Update Client" : "Add Client"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Button
            onClick={handleSendEmailToAll}
            disabled={isSendingEmails || filteredClients.length === 0}
            className="gap-2"
          >
            {isSendingEmails ? (
              <span className="animate-pulse">Sending...</span>
            ) : (
              <>
                <span>📧</span>
                <span>Email All Clients</span>
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <Input
          placeholder="Search clients by name, email, company, etc..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          className="max-w-md"
        />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableCaption>
            Client list ({filteredClients.length} total)
          </TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currentClients.length > 0 ? (
              currentClients.map((client) => (
                <TableRow key={client.id}>
                  <TableCell className="font-medium">{client.name}</TableCell>
                  <TableCell>{client.company}</TableCell>
                  <TableCell>{client.email}</TableCell>
                  <TableCell>{client.phone}</TableCell>
                  <TableCell>
                    {client.city}, {client.state} {client.zip_code}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        client.status === "active" ? "default" : "secondary"
                      }
                    >
                      {client.status || "active"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingClient(client);
                        setIsDialogOpen(true);
                      }}
                    >
                      <Edit className="h-4 w-4 mr-1" /> Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-500 hover:bg-red-50"
                      onClick={() => {
                        if (
                          confirm(
                            "Are you sure you want to delete this client?"
                          )
                        ) {
                          handleDelete(client.id);
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="text-center py-8 text-muted-foreground"
                >
                  {clients.length === 0
                    ? "No clients found"
                    : "No matching clients found"}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="mt-6 flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            Showing {indexOfFirst + 1}-
            {Math.min(indexOfLast, filteredClients.length)} of{" "}
            {filteredClients.length} clients
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
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
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
