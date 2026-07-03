import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Payment } from "../api/types";
import { DataTable } from "../components/DataTable";
import { PageShell } from "../components/PageShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatCurrency, formatDate } from "../utils/format";
import { useResource } from "./useResource";

export function PaymentsPage() {
  const { t } = useTranslation();
  const { data, loading, error } = useResource<Payment[]>(useCallback(() => api.payments(), []));

  return (
    <PageShell title={t("payments.title")} subtitle={t("payments.subtitle")}>
      {loading && <div className="skeleton-table" />}
      {error && <div className="form-error">{error}</div>}
      {data && (
        <DataTable
          rows={data}
          columns={[
            { key: "match", header: t("payments.match"), render: (payment) => `#${payment.match_id}` },
            { key: "payer", header: t("payments.payer"), render: (payment) => `#${payment.payer_id}` },
            { key: "amount", header: t("payments.amount"), render: (payment) => formatCurrency(payment.amount) },
            { key: "method", header: t("payments.method"), render: (payment) => t(`paymentMethods.${payment.payment_method}`) },
            { key: "status", header: t("common.status"), render: (payment) => <StatusBadge value={payment.payment_status} /> },
            { key: "created", header: t("common.createdAt"), render: (payment) => formatDate(payment.created_at) }
          ]}
        />
      )}
    </PageShell>
  );
}
