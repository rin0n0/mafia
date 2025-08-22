import { defineStore } from "pinia";

interface Notification {
  id: number;
  message: string;
}

interface UiState {
  notifications: Notification[];
}

let notificationId = 0;

export const useUiStore = defineStore("ui", {
  state: (): UiState => ({
    notifications: [],
  }),
  actions: {
    addNotification(message: string, duration = 4000) {
      const id = notificationId++;
      this.notifications.push({ id, message });

      setTimeout(() => {
        this.removeNotification(id);
      }, duration);
    },
    removeNotification(id: number) {
      this.notifications = this.notifications.filter((n) => n.id !== id);
    },
  },
});
