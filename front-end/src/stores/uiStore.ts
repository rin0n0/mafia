import { defineStore } from "pinia";
import { ref } from "vue";

interface Notification {
  id: number;
  message: string;
}

let notificationId = 0;

export const useUiStore = defineStore("ui", () => {
  const notifications = ref<Notification[]>([]);

  function addNotification(message: string, duration = 4000) {
    const id = notificationId++;
    notifications.value.push({ id, message });

    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }

  function removeNotification(id: number) {
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }

  return {
    notifications,
    addNotification,
    removeNotification,
  };
});
