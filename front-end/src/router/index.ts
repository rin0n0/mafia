import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import LobbyView from "../views/LobbyView.vue"; 
import RoomView from "../views/RoomView.vue"; 

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "lobby",
    component: LobbyView,
    meta: {
      title: 'Главная'
    }
  },
  {
    path: "/room/:id", 
    name: "room",
    component: RoomView,
    props: true,
    meta: {
      title: "Комната"
    }
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  document.title = (to.meta.title as string) || 'Мафия';
  next();
});

export default router;
