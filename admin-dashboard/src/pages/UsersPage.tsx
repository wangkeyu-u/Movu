import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { User } from "../api/types";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function UsersPage() {
  const { t } = useTranslation();
  const { data, loading, error, reload } = useResource<User[]>(useCallback(() => api.users(), []));
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyUserId, setBusyUserId] = useState<number | null>(null);

  async function run(userId: number, action: Promise<unknown>) {
    setActionError(null);
    setBusyUserId(userId);
    try {
      await action;
      reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : t("common.error"));
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <PageShell title={t("users.title")} subtitle={t("users.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {actionError && <div className="form-error">{actionError}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "name", header: t("users.name"), render: (user) => <strong>{user.name}</strong> },
            { key: "email", header: t("users.email"), render: (user) => user.email },
            { key: "role", header: t("users.role"), render: (user) => t(`roles.${user.role}`) },
            { key: "rating", header: t("users.rating"), render: (user) => user.rating.toFixed(1) },
            { key: "emailVerified", header: t("users.emailVerified"), render: (user) => <StatusBadge value={user.email_verified} /> },
            {
              key: "verification",
              header: t("users.verification"),
              render: (user) => <StatusBadge value={user.verification_status} />
            },
            { key: "banned", header: t("users.banned"), render: (user) => <StatusBadge value={user.is_banned} /> },
            { key: "created", header: t("common.createdAt"), render: (user) => formatDate(user.created_at) },
            {
              key: "actions",
              header: t("common.actions"),
              render: (user) => (
                <div className="action-row">
                  <ActionButton
                    disabled={busyUserId === user.user_id || user.verification_status === "approved"}
                    onClick={() => run(user.user_id, api.verifyUser(user.user_id, "approved"))}
                  >
                    {t("common.approve")}
                  </ActionButton>
                  <ActionButton
                    disabled={busyUserId === user.user_id || user.verification_status === "rejected"}
                    onClick={() => run(user.user_id, api.verifyUser(user.user_id, "rejected"))}
                  >
                    {t("common.reject")}
                  </ActionButton>
                  {user.is_banned ? (
                    <ActionButton disabled={busyUserId === user.user_id} onClick={() => run(user.user_id, api.unbanUser(user.user_id))}>
                      {t("common.unban")}
                    </ActionButton>
                  ) : (
                    <ActionButton disabled={busyUserId === user.user_id} variant="danger" onClick={() => run(user.user_id, api.banUser(user.user_id))}>
                      {t("common.ban")}
                    </ActionButton>
                  )}
                </div>
              )
            }
          ]}
        />
      )}
    </PageShell>
  );
}
