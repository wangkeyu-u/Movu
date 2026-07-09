import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, Input } from "@movu/ui";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  getSearchText?: (row: T) => string;
  pageSize?: number;
  exportFilename?: string;
}

export function DataTable<T>({ rows, columns, getSearchText = defaultSearchText, pageSize = 20, exportFilename = "movu-records.csv" }: DataTableProps<T>) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return rows;
    return rows.filter((row) => getSearchText(row).toLowerCase().includes(normalizedQuery));
  }, [getSearchText, query, rows]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  function updateQuery(value: string) {
    setQuery(value);
    setPage(1);
  }

  function exportCsv() {
    const csv = [
      columns.map((column) => csvCell(column.header)).join(","),
      ...filteredRows.map((row) => columns.map((column) => csvCell(renderPlainText(column.render(row)))).join(","))
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = exportFilename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!rows.length) {
    return <div className="empty-state">{t("common.empty")}</div>;
  }

  return (
    <section className="data-table-shell">
      <div className="table-toolbar">
        <Input value={query} onChange={(event) => updateQuery(event.target.value)} placeholder={t("common.searchRecords")} aria-label={t("common.searchRecords")} />
        <div className="table-actions">
          <span>{t("common.showingRecords", { shown: pagedRows.length, total: filteredRows.length })}</span>
          <Button variant="secondary" type="button" onClick={exportCsv}>
            {t("common.exportCsv")}
          </Button>
        </div>
      </div>
      {!filteredRows.length ? (
        <div className="empty-state">{t("common.noSearchResults")}</div>
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.key}>{column.header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pagedRows.map((row, index) => (
                  <tr key={index}>
                    {columns.map((column) => (
                      <td key={column.key}>{column.render(row)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-pagination">
            <Button variant="secondary" type="button" disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
              {t("common.previous")}
            </Button>
            <span>{t("common.pageStatus", { page: currentPage, pages: totalPages })}</span>
            <Button variant="secondary" type="button" disabled={currentPage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>
              {t("common.next")}
            </Button>
          </div>
        </>
      )}
    </section>
  );
}

function defaultSearchText<T>(row: T): string {
  try {
    return JSON.stringify(row);
  } catch {
    return String(row);
  }
}

function renderPlainText(value: ReactNode): string {
  if (value === null || value === undefined || typeof value === "boolean") return "";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(renderPlainText).join(" ");
  if (typeof value === "object" && "props" in value) {
    const props = (value as { props?: { children?: ReactNode } }).props;
    return renderPlainText(props?.children);
  }
  return "";
}

function csvCell(value: string): string {
  return `"${value.replace(/"/g, '""')}"`;
}
