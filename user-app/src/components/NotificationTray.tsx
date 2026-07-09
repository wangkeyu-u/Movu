import { Button, Card } from "@movu/ui";
import { Bell, CheckCheck, Inbox } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { Notification as AppNotification } from "../api/types";
import { formatDateTime } from "../utils/format";

export function NotificationTray() {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">(
    "Notification" in window ? window.Notification.permission : "unsupported"
  );
  const seenNotificationIds = useRef<Set<number>>(new Set());
  const initialized = useRef(false);

  async function reload() {
    try {
      const [notifications, unread] = await Promise.all([api.notifications(), api.unreadNotifications()]);
      announceNewNotifications(notifications);
      setItems(notifications);
      setUnreadCount(unread.unread_count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.somethingWrong"));
    }
  }

  async function markRead(notificationId: number) {
    await api.markNotificationRead(notificationId);
    reload();
  }

  async function markAllRead() {
    await api.markAllNotificationsRead();
    reload();
  }

  async function enableDesktopNotifications() {
    if (!("Notification" in window)) {
      setPermission("unsupported");
      return;
    }
    const nextPermission = await window.Notification.requestPermission();
    setPermission(nextPermission);
  }

  function announceNewNotifications(notifications: AppNotification[]) {
    const unreadNotifications = notifications.filter((item) => !item.read_at);
    if (!initialized.current) {
      unreadNotifications.forEach((item) => seenNotificationIds.current.add(item.notification_id));
      initialized.current = true;
      return;
    }
    unreadNotifications
      .filter((item) => !seenNotificationIds.current.has(item.notification_id))
      .forEach((item) => {
        seenNotificationIds.current.add(item.notification_id);
        if ("Notification" in window && window.Notification.permission === "granted") {
          new window.Notification(item.title, { body: item.body, tag: `movu-${item.notification_id}` });
        }
      });
  }

  useEffect(() => {
    reload();
    const interval = window.setInterval(reload, 30000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="notification-tray">
      <Button className="notification-trigger" variant="icon" type="button" aria-label={t("common.notifications")} onClick={() => setOpen((value) => !value)}>
        <Bell size={18} aria-hidden="true" />
        {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
      </Button>
      {open && (
        <Card className="notification-popover">
          <div className="notification-head">
            <strong>{t("notifications.title")}</strong>
            <Button variant="ghost" type="button" onClick={markAllRead}>
              <CheckCheck size={15} aria-hidden="true" />
              {t("notifications.markAll")}
            </Button>
          </div>
          <Button className="desktop-notification-button" variant="secondary" type="button" onClick={enableDesktopNotifications} disabled={permission === "granted" || permission === "unsupported"}>
            {permission === "granted" ? t("notifications.desktopEnabled") : permission === "unsupported" ? t("notifications.desktopUnsupported") : t("notifications.enableDesktop")}
          </Button>
          {error && <p className="inline-error">{error}</p>}
          {!items.length && (
            <div className="empty-copy">
              <Inbox size={17} aria-hidden="true" />
              {t("notifications.empty")}
            </div>
          )}
          <div className="notification-list">
            {items.map((item) => (
              <Button
                variant="ghost"
                className={`notification-item ${item.read_at ? "" : "unread"}`}
                key={item.notification_id}
                type="button"
                onClick={() => markRead(item.notification_id)}
              >
                <span>{t(`notifications.categories.${item.category}`, { defaultValue: item.category })}</span>
                <strong>{item.title}</strong>
                <p>{item.body}</p>
                <small>{formatDateTime(item.created_at, i18n.language === "en" ? "en-MY" : i18n.language)}</small>
              </Button>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
