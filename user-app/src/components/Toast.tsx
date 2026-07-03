import { Alert } from "@movu/ui";

export function Toast({ message, tone = "info" }: { message: string | null; tone?: "info" | "error" | "success" }) {
  if (!message) return null;
  return <Alert tone={tone}>{message}</Alert>;
}
