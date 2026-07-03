export function formatDateTime(value: string, locale = "en-MY"): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function toLocalInputValue(date = new Date(Date.now() + 60 * 60 * 1000)): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function fromLocalInputValue(value: string): string {
  return new Date(value).toISOString();
}

export function statusKey(value: string | boolean): string {
  return String(value);
}
