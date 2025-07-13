import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";

import { useUserStore } from "./stores/userStore";

import '@/assets/styles/global.css'; 

const pinia = createPinia();
const app = createApp(App);

app.use(pinia);
app.use(router);

const userStore = useUserStore();
userStore.initialization();
app.mount("#app");
