import type { User } from "../api/types";

export type AccessIssue = "email_unverified" | "pending" | "rejected" | "banned" | "driver_only";

export function getAccessIssue(user: User | null): AccessIssue | null {
  if (!user) return null;
  if (user.is_banned) return "banned";
  if (!user.email_verified) return "email_unverified";
  if (user.verification_status === "pending") return "pending";
  if (user.verification_status === "rejected") return "rejected";
  return null;
}

export function canUseCoreActions(user: User | null): boolean {
  return getAccessIssue(user) === null;
}
