// lib/axiosLocal.ts
import axios from "axios";

const axiospermit = axios.create({
  baseURL: process.env.NEXT_PUBLIC_LOCAL_API_URL,
});

export default axiospermit;
