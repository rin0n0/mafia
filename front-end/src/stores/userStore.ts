import { defineStore } from "pinia";
import { v4 as uuidv4 } from "uuid";
import { ref, readonly } from "vue"; // Добавляем readonly для безопасности

// Сообщаем TypeScript о существовании глобального объекта Telegram WebApp
declare global {
  interface Window {
    Telegram: any;
  }
}

export const useUserStore = defineStore("user", () => {
  // --- STATE ---
  // Делаем эти значения `readonly` для внешнего мира.
  // Изменять их можно только через actions стора.
  const _clientId = ref<string | null>(null);
  const _playerName = ref<string>("");

  // --- GETTERS ---
  const clientId = readonly(_clientId);
  const playerName = readonly(_playerName);

  // --- ACTIONS ---

  /**
   * Инициализирует состояние пользователя.
   * Проверяет, запущено ли приложение как Telegram Mini App,
   * и использует данные оттуда, если они доступны.
   * В противном случае использует localStorage.
   */
  function initialization() {
    // 1. Попытка инициализации из Telegram
    try {
      if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        const tgUser = tg.initDataUnsafe?.user;

        if (tgUser && tgUser.id) {
          console.log("Running in Telegram context. User:", tgUser);
          _clientId.value = String(tgUser.id);

          // Берем имя из Telegram, если в localStorage еще нет кастомного имени
          const savedName = localStorage.getItem("mafiaPlayerName");
          _playerName.value = savedName || tgUser.first_name || "Игрок";

          // Сохраняем Telegram ID в localStorage для консистентности
          localStorage.setItem("mafiaClientId", _clientId.value);
          if (!savedName) {
            localStorage.setItem("mafiaPlayerName", _playerName.value);
          }

          // Сообщаем Telegram, что приложение готово и должно расшириться
          tg.ready();
          tg.expand();
          return; // Завершаем, если инициализация из TG прошла успешно
        }
      }
    } catch (error) {
      console.error("Failed to initialize from Telegram WebApp:", error);
    }

    // 2. Фолбэк на localStorage (если мы не в Telegram)
    console.log("Running in standard browser context.");
    let id = localStorage.getItem("mafiaClientId");
    if (!id) {
      id = uuidv4();
      localStorage.setItem("mafiaClientId", id);
    }
    _clientId.value = id;

    const name = localStorage.getItem("mafiaPlayerName");
    if (name) {
      _playerName.value = name;
    }
  }

  /**
   * Устанавливает и сохраняет имя игрока.
   * @param name Новое имя игрока.
   */
  function setPlayerName(name: string | undefined) {
    if (!name) return;

    const trimmedName = name.slice(0, 20); // Обрезаем до 20 символов

    if (trimmedName.length < 3) {
      // Можно либо ничего не делать, либо установить обрезанное имя,
      // если оно все еще валидно. Оставим return для строгой валидации.
      return;
    }

    _playerName.value = trimmedName;
    localStorage.setItem("mafiaPlayerName", trimmedName);
  }

  return {
    // Getters
    clientId,
    playerName,
    // Actions
    initialization,
    setPlayerName,
  };
});
