import { ref, watch, onUnmounted } from "vue";

export function useTypewriter(textToType: () => string) {
  const displayedText = ref("");
  const isTyping = ref(false);
  let intervalId: number | null = null;

  const startTyping = () => {
    stopTyping();
    const fullText = textToType();
    if (!fullText) {
      displayedText.value = "";
      isTyping.value = false;
      return;
    }

    displayedText.value = "";
    isTyping.value = true;
    let i = 0;

    intervalId = window.setInterval(() => {
      if (i < fullText.length) {
        displayedText.value += fullText.charAt(i);
        i++;
      } else {
        stopTyping();
      }
    }, 50);
  };

  const stopTyping = () => {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    isTyping.value = false;
  };

  watch(textToType, startTyping, { immediate: true });
  onUnmounted(stopTyping);

  return { displayedText, isTyping };
}
