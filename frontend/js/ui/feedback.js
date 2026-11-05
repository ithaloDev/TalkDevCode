export function toast(message, type = "success") {
  const region = document.getElementById("toast-region");
  if (!region) return;
  const item = document.createElement("div");
  item.className = `toast ${type === "error" ? "error" : ""}`;
  item.setAttribute("role", type === "error" ? "alert" : "status");
  item.textContent = message;
  region.append(item);
  window.setTimeout(() => item.remove(), 4200);
}

export function parseApiDate(value) {
  if (!value) return null;
  // SQLite pode retornar DATETIME sem offset; nesse contrato, valores sem fuso são UTC.
  const normalized = typeof value === "string" && !/(Z|[+-]\d{2}:?\d{2})$/i.test(value)
    ? `${value.replace(" ", "T")}Z`
    : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value) {
  const date = parseApiDate(value);
  if (!date) return "";

  const differenceMs = date.getTime() - Date.now();
  const absoluteMs = Math.abs(differenceMs);
  if (absoluteMs < 60_000) return "Agora mesmo";

  const differenceSeconds = Math.round(differenceMs / 1000);
  const units = [
    { limit: 3600, divisor: 60, unit: "minute" },
    { limit: 86400, divisor: 3600, unit: "hour" },
    { limit: 604800, divisor: 86400, unit: "day" },
    { limit: 2629800, divisor: 604800, unit: "week" },
    { limit: 31557600, divisor: 2629800, unit: "month" },
    { limit: Infinity, divisor: 31557600, unit: "year" },
  ];
  const selected = units.find((item) => absoluteMs < item.limit * 1000) || units.at(-1);
  const amount = Math.round(differenceSeconds / selected.divisor);
  return new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" }).format(amount, selected.unit);
}

export function refreshRelativeTimes(root = document) {
  root.querySelectorAll("time[data-relative-time]").forEach((element) => {
    element.textContent = formatDate(element.dateTime || element.dataset.relativeTime);
  });
}

export function initials(value = "U") {
  return value.trim().slice(0, 1).toLocaleUpperCase("pt-BR");
}
