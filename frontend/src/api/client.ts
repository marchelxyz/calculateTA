import axios from "axios";

const client = axios.create({
  baseURL: "/api",
});

client.interceptors.request.use((config) => {
  const username = localStorage.getItem("auth_username");
  const password = localStorage.getItem("auth_password");
  if (username && password) {
    const token = btoa(`${username}:${password}`);
    config.headers = {
      ...config.headers,
      Authorization: `Basic ${token}`,
    };
  }
  return config;
});

export default client;
