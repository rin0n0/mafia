import asyncio
import json
import logging
from typing import Dict, List

from google.genai import Client, types, errors

from schemas import AINarration, AIContext
from config import settings # Используем централизованный конфиг

logger = logging.getLogger(__name__)

API_TIMEOUT = 25.0

class AINarrator:
    def __init__(self):
        self._api_key = settings.GEMINI_API_KEY
        if not self._api_key:
            logger.warning("GEMINI_API_KEY is not set in .env file. AI Narrator will use fallback mode.")
        
        # Базовые настройки, которые не меняются
        self._base_config = {
            "thinking_config": types.ThinkingConfig(thinking_budget=0),
            "safety_settings": [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
            "temperature": 0.7,
            "response_schema": AINarration,
            "response_mime_type": "application/json",
        }

    async def generate_narration(
        self,
        context: AIContext,
        event_type: str,
        event_data: Dict
    ) -> AINarration:
        if not self._api_key:
            return self._get_fallback_narration(event_type, event_data)

        try:
            async with asyncio.timeout(API_TIMEOUT):
                system_instruction, contents = self._generate_prompt(context, event_type, event_data)
                
                request_config = self._base_config.copy()
                request_config["system_instruction"] = system_instruction
                
                async with Client(api_key=self._api_key).aio as aclient:
                    # Используем НЕ-стриминговую версию
                    response = await aclient.models.generate_content(
                        model='gemini-flash-latest',
                        contents=contents,
                        config=request_config
                    )
                    
                    # R --- ВОТ ОНО, ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ---
                    try:
                        # Просто берем текст ответа и парсим его как JSON
                        parsed_json = json.loads(response.text)
                        return AINarration(**parsed_json)
                    except (json.JSONDecodeError, TypeError) as e:
                        # Если Gemini вернул невалидный JSON, логируем и используем фолбэк
                        logger.error(f"AI Narrator failed to parse JSON from response. Error: {e}. Response text: {response.text}")
                        return self._get_fallback_narration(event_type, event_data)

        except asyncio.TimeoutError:
            logger.error(f"AI Narrator timed out after {API_TIMEOUT} seconds.")
            return self._get_fallback_narration(event_type, event_data)
        except (errors.APIError, Exception) as e:
            logger.error(f"An error occurred in AI Narrator: {e}", exc_info=True)
            return self._get_fallback_narration(event_type, event_data)

    def _generate_prompt(self, context: AIContext, event_type: str, event_data: Dict) -> tuple[str, List[types.Content]]:
        descriptions_text = "\n".join([f"- {name}: {desc}" for name, desc in context.player_descriptions.items()])
        system_instruction = (
            f"Ты — беспристрастный рассказчик, ведущий игры 'Мафия'. Твой стиль повествования — '{context.setting}'. "
            f"Вот персонажи в твоей истории:\n{descriptions_text}\n"
            "Твоя задача — красочно описывать игровые события. Ты должен быть креативным и активно использовать описания персонажей. "
            "Никогда не упоминай игровые роли (мафия, доктор), если их нет в явном запросе. "
            "Всегда отвечай в формате JSON."
        )

        contents = []
        if context.history:
            history_text = "\n".join([f"- {entry}" for entry in context.history])
            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=f"Краткая история предыдущих событий:\n{history_text}")]))

        user_query = self._get_user_query(event_type, event_data)
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_query)]))
        
        return system_instruction, contents

    def _get_user_query(self, event_type: str, event_data: Dict) -> str:
        victim = event_data.get('victim_name')
        length_constraint = "Ответь кратко, не более 2-3 предложений."

        queries = {
            "game_start": f"Игра начинается. Напиши приветственное атмосферное вступление. {length_constraint}",
            "night_kill": f"Произошло событие 'убийство ночью'. Жертва — {victim}. Опиши эту сцену. {length_constraint}",
            "night_save": f"Произошло событие 'спасение ночью'. Мафия пыталась убить игрока {victim or 'некую цель'}, но его спасли. Опиши это. {length_constraint}",
            "night_no_kill": f"Этой ночью никто не умер. Опиши эту тихую, но напряженную ночь. {length_constraint}",
            "lynch_victim": f"Произошло событие 'казнь'. Городская толпа решила казнить игрока {victim}. Опиши сцену казни. {length_constraint}",
            "lynch_tie": f"Дневное голосование за казнь закончилось ничьей. Опиши, как голоса разделились. {length_constraint}",
            "joke_voting_start": "Сейчас начнется шуточное голосование. Придумай и задай игрокам безобидный вопрос связанный с сеттингом (в поле 'summary'), ответом на который будет имя одного из них.",
            "joke_vote_result": f"Шуточное голосование завершилось. Самым подозрительным посчитали игрока {victim}. Опиши реакцию города. {length_constraint}",
            "joke_vote_tie": f"Шуточное голосование закончилось ничьей. Опиши, как мнения разделились. {length_constraint}",
            "day_start": f"Начинается новый день. Опиши, как город просыпается. {length_constraint}",
            "night_start": f"Наступает ночь. Опиши, как город погружается во тьму. {length_constraint}",
            "voting_start": f"Начинается дневное голосование. Опиши призыв к голосованию. {length_constraint}",
        }
        return queries.get(event_type, f"Опиши текущую ситуацию в городе. {length_constraint}")

    def _get_fallback_narration(self, event_type: str, event_data: Dict) -> AINarration:
        logger.info(f"Using fallback narration for event: {event_type}")
        victim_name = event_data.get("victim_name", "один из жителей")
        
        fallbacks = {
            "game_start": AINarration(title="Начало игры", summary="Ведущий приветствует игроков.", narration="Добро пожаловать в игру. Город засыпает, открывая сцену для тайн и интриг. Сделайте свой первый ход."),
            "night_kill": AINarration(title="Потеря в ночи", summary=f"Ночью был убит игрок {victim_name}.", narration=f"С наступлением утра город обнаружил, что {victim_name} стал очередной жертвой безжалостной мафии."),
            "night_save": AINarration(title="На волосок от смерти", summary=f"Было совершено покушение на игрока {victim_name}, но он был спасен.", narration=f"Темные силы пытались унести еще одну жизнь, но {victim_name} чудом избежал гибели."),
            "night_no_kill": AINarration(title="Затишье перед бурей", summary="Этой ночью никто не умер.", narration="Город провел ночь в напряженном затишье. Никто не был убит, но чувство опасности лишь усилилось."),
            "lynch_victim": AINarration(title="Приговор толпы", summary=f"Дневным голосованием был казнен игрок {victim_name}.", narration=f"По итогам дневного голосования, гнев толпы обрушился на {victim_name}. Его судьба решена."),
            "joke_voting_start": AINarration(title="Первые подозрения", summary="Кто кажется вам самым подозрительным?", narration="Пришло время поделиться первыми впечатлениями. Выберите того, кто кажется вам наиболее подозрительным."),
        }
        
        return fallbacks.get(event_type, AINarration(title="Событие", summary="Произошло игровое событие.", narration="Ведущий подводит итоги..."))

ai_narrator = AINarrator()