import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LobbyView from "../views/LobbyView.vue"; 
import RoomView from "../views/RoomView.vue"; 

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "lobby",
    component: LobbyView,
  },
  {
    path: "/room/:id", 
    name: "room",
    component: RoomView,
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
