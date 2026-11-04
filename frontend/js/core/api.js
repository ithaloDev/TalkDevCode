const DEFAULT_API_URL = window.location.port === "5500"
  ? "http://127.0.0.1:8000/api/v1"
  : `${window.location.origin}/api/v1`;

export class ApiError extends Error {
  constructor(message, status = 0, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export class ApiClient {
  constructor(baseUrl = window.TALKDEV_API_URL || DEFAULT_API_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async request(path, { method = "GET", body, token, signal } = {}) {
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;

    let response;
    try {
      response = await fetch(`http://127.0.0.1:8000/api/v1${path}`, {
        method, 
        headers, 
        signal,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new ApiError("Não foi possível conectar à API. Verifique se o servidor está ativo.");
    }

    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : null;

    if (!response.ok) {
      const detail = payload?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg).join(" ")
        : (typeof detail === "string" ? detail : `A solicitação falhou (${response.status}).`);
      throw new ApiError(message, response.status, payload);
    }
    return payload;
  }

  get(path, options = {}) { return this.request(path, options); }
  post(path, body, options = {}) { return this.request(path, { ...options, method: "POST", body }); }
  put(path, body, options = {}) { return this.request(path, { ...options, method: "PUT", body }); }
  delete(path, options = {}) { return this.request(path, { ...options, method: "DELETE" }); }
}

export const api = new ApiClient();
