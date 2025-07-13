<!-- src/App.vue -->
<template>
  <router-view/>
</template>

<style>
/* 
  Глобальный CSS Reset. 
  Этот код убирает все стандартные отступы браузера.
*/
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 
  Применяем базовые стили ко всему приложению.
  Это лучшее место для указания глобального шрифта.
*/
html, body, #app {
  height: 100%;
  width: 100%;
  font-family: 'Montserrat', sans-serif;
}
</style>