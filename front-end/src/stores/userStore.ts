import { defineStore } from "pinia";
import { v4 as uuidv4 } from "uuid";

interface UserState {
  clientId: string | null;
  playerName: string;
}

export const useUserStore = defineStore("user", {
  state: (): UserState => ({
    clientId: null,
    playerName: "",
  }),
  actions: {
    initialization() {
      let id = localStorage.getItem("mafiaClientId");
      const name = localStorage.getItem("mafiaPlayerName");

      if (!id) {
        id = uuidv4();
        localStorage.setItem("mafiaClientId", id);
      }

      this.clientId = id;
      if (name) {
        this.playerName = name;
      }
    },

    setPlayerName(name: string | undefined) {
      if (name) {
        this.playerName = name;
      localStorage.setItem("mafiaPlayerName", name);
      }
    },
  },
});
