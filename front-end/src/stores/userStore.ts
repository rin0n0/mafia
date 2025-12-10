import { defineStore } from "pinia";
import { v4 as uuidv4 } from "uuid";
import { ref } from "vue";

export const useUserStore = defineStore("user", () => {
  const clientId = ref<string | null>(null);
  const playerName = ref<string>("");

  function initialization() {
    let id = localStorage.getItem("mafiaClientId");
    const name = localStorage.getItem("mafiaPlayerName");

    if (!id) {
      id = uuidv4();
      localStorage.setItem("mafiaClientId", id);
    }

    clientId.value = id;
    if (name) {
      playerName.value = name;
    }
  }

  function setPlayerName(name: string | undefined) {
    if (name) {
      if (name.length > 20) {
        name = name.slice(0, 20);
      }
      if (name.length < 3) {
        return;
      }
      playerName.value = name;
      localStorage.setItem("mafiaPlayerName", name);
    }
  }

  return {
    clientId,
    playerName,
    initialization,
    setPlayerName,
  };
});
