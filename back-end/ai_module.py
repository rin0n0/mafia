import asyncio
import json
import logging
from typing import Dict, List, Optional

from google.genai import Client, types, errors

from schemas import AINarration, AIContext
from config import settings 

logger = logging.getLogger(__name__)

API_TIMEOUT = 12.0

class AINarrator:
    def __init__(self):
        self._default_api_key = settings.GEMINI_API_KEY
        if not self._default_api_key:
            logger.warning("GEMINI_API_KEY is not set in .env file. AI Narrator will use fallback mode.")

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
        event_data: Dict,
        api_key: Optional[str] = None
    ) -> AINarration:
        self._default_api_key = settings.GEMINI_API_KEY
        effective_api_key = api_key if api_key else self._default_api_key
        if not self._default_api_key:
            logger.warning("GEMINI_API_KEY is not set in .env file. AI Narrator will use fallback mode.")
        try:
            async with asyncio.timeout(API_TIMEOUT):
                system_instruction, contents = self._generate_prompt(context, event_type, event_data)
                
                request_config = self._base_config.copy()
                request_config["system_instruction"] = system_instruction
                
                async with Client(api_key=effective_api_key).aio as aclient:
                    response = await aclient.models.generate_content(
                        model='gemini-flash-latest',
                        contents=contents,
                        config=request_config
                    )
                    
                    try:
                        parsed_json = json.loads(response.text)
                        return AINarration(**parsed_json)
                    except (json.JSONDecodeError, TypeError) as e:
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
            f"# Ты — беспристрастный рассказчик, ведущий игры 'Мафия'. Твой стиль повествования должен соответствовать сеттингу — '{context.setting}'.\n"
            f"Вот персонажи в твоей истории:\n{descriptions_text}\n"
            "1. Твоя задача — создавать цельную, развивающуюся историю. Ссылайся на прошлые события"
            "2. ИЗБЕГАЙ ПОВТОРОВ. Не используй одни и те же метафоры и речевые обороты, которые ты уже использовал в истории.\n"
            "3. Будь креативен, используй информация из описания персонажей для окраски событий.Учитывай живы ли они или они уже выбыли из игры\n"
            "4. Не упоминай игровые роли (мафия, доктор и другие), если это не указано явно.\n"
            "5. Всегда отвечай в формате JSON."
        )

        contents = []
        if context.history:
            previous_text = "\n---\n".join(context.history)
            history_context = (
                f"КОНТЕКСТ ПРЕДЫДУЩИХ ГЛАВ (Твой прошлый текст):\n"
                f"{previous_text}\n"
                f"---\n"
                f"Продолжи историю, не повторяясь."
            )
            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=history_context)]))

        user_query = self._get_user_query(event_type, event_data)
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_query)]))
        
        return system_instruction, contents

    def _get_user_query(self, event_type: str, event_data: Dict) -> str:
        victim = event_data.get('victim_name', 'кто-то из присутствующих')
        winner = event_data.get('winner_team', 'одна из сторон')
        
        length_constraint = "Ответь кратко, не более 2-3 предложений."
        
        style_instruction = "Используй терминологию и атмосферу текущего сеттинга. Избегай слов 'город' или 'жители', если они не подходят к сеттингу."

        base_templates = {
            "game_start": (
                f"Игра начинается. Опиши локацию и текущую атмосферу в сеттинге. "
                f"Введи игроков в курс дела, создай ощущение надвигающейся тайной угрозы. {length_constraint}"
            ),

            "night_kill": (
                f"Произошло событие 'убийство'. Жертва — {victim}. "
                f"Опиши сцену обнаружения тела или исчезновения персонажа. "
                f"Сфокусируйся на реакции выживших и деталях места преступления в рамках сеттинга. {length_constraint}"
            ),
            "night_save": (
                f"Было совершено покушение на игрока {victim or 'некую цель'}, но защита сработала. "
                f"Опиши это как чудесное спасение, осечку врага или вмешательство третьей силы. "
                f"Жертва жива. {length_constraint}"
            ),
            "night_no_kill": (
                f"Период опасности прошел, и все живы. "
                f"Опиши это как напряженное затишье, подозрительную тишину или ложное чувство безопасности. {length_constraint}"
            ),

            "lynch_victim": (
                f"Сообщество приняло коллективное решение устранить игрока {victim}. "
                f"Опиши, как именно приводится в исполнение этот приговор в данном сеттинге (казнь, изгнание, арест и т.д.). "
                f"Сделай акцент на фатальности этого выбора. {length_constraint}"
            ),
            "lynch_tie": (
                f"Голосование за устранение зашло в тупик. Мнения разделились, и единого решения нет. "
                f"Опиши этот раскол в сообществе, споры и нарастающее недоверие. Никто не устранен. {length_constraint}"
            ),

            "joke_voting_start": (
                f"Сейчас начнется предварительное обсуждение. Твоя задача — придумать провокационный или философский вопрос, "
                f"подходящий под сеттинг, ответом на который будет имя кого-то из присутствующих. "
                f"Верни этот вопрос в поле 'summary'. Не называй имен сам. {length_constraint}"
            ),
            
            "joke_vote_result": (
                f"Голосование по твоему предыдущему вопросу завершилось. Большинство указало на игрока {victim}. "
                f"Опиши этот результат, связывая его с сутью заданного тобой вопроса. "
                f"Как окружающие теперь смотрят на {victim}? {length_constraint}"
            ),
            "joke_vote_tie": (
                f"Голосование по твоему вопросу не выявило лидера. "
                f"Люди (или существа) указали на разных, голоса распылились. "
                f"Опиши это замешательство и отсутствие единства во мнениях. {length_constraint}"
            ),

            "day_start": (
                f"Начинается активная фаза (день/утро/смена). Опиши, как локация оживает после периода опасности. "
                f"Выжившие собираются вместе. {length_constraint}"
            ),
            "night_start": (
                f"Начинается фаза опасности (ночь/отбой/тьма). Опиши, как локация погружается в тревожное состояние. "
                f"Мирные жители ищут убежище, а угроза выходит на охоту. {length_constraint}"
            ),
            "voting_start": (
                f"Время обсуждений вышло. Наступает момент принятия решения. "
                f"Призови присутствующих сделать свой выбор и определить виновного. {length_constraint}"
            ),
            
            "game_over": (
                f"История завершена. Победившая сторона: {winner}. "
                f"Опиши эпилог этой драмы. Что стало с этой локацией и выжившими? "
                f"Подведи красивый, литературный итог. {length_constraint}"
            ),
        }
        
        additional_instructions = []
        whore_target = event_data.get('whore_target_name')
        if whore_target and event_type in ["night_kill", "night_save", "night_no_kill"]:
            additional_instructions.append(
                f"Вплети в рассказ деталь: игрок {whore_target} был отвлечен визитом "
                f"Ночной Бабочки (или аналога в сеттинге) и пропустил всё происходящее."
            )
        base_text = base_templates.get(event_type, "Опиши текущую ситуацию.")
        extras_text = " ".join(additional_instructions)
        constraints = "Ответь кратко, не более 3-4 предложений. Используй терминологию сеттинга."

        return f"{base_text} {extras_text} {constraints} {style_instruction}"

    def _get_fallback_narration(self, event_type: str, event_data: Dict) -> AINarration:
        logger.info(f"Using fallback narration for event: {event_type}")
        winner = event_data.get('winner_team')
        victim = event_data.get("victim_name", "один из жителей")
        
        base_templates = {
            "game_start": {
                "title": "Начало игры",
                "summary": "Ведущий приветствует игроков.",
                "narration": "Добро пожаловать в игру. Город засыпает, открывая сцену для тайн и интриг. Сделайте свой первый ход."
            },
            "night_kill": {
                "title": "Потеря в ночи",
                "summary": f"Ночью был убит игрок {victim}.",
                "narration": f"С наступлением утра город обнаружил, что {victim} стал очередной жертвой безжалостной мафии."
            },
            "night_save": {
                "title": "На волосок от смерти",
                "summary": f"Было совершено покушение на игрока {victim}, но он был спасен.",
                "narration": f"Темные силы пытались унести еще одну жизнь, но {victim} чудом избежал гибели."
            },
            "night_no_kill": {
                "title": "Затишье перед бурей",
                "summary": "Этой ночью никто не умер.",
                "narration": "Город провел ночь в напряженном затишье. Никто не был убит, но чувство опасности лишь усилилось."
            },
            "night_start": {
                "title": "Наступает ночь",
                "summary": "Город засыпает.",
                "narration": "Тени удлиняются, и на улицы выходит зло. Мирные жители спешат по домам, надеясь пережить эту ночь."
            },
            "day_start": {
                "title": "Новый день",
                "summary": "Город просыпается.",
                "narration": "Солнце встает, освещая улицы. Жители собираются, чтобы обсудить ночные происшествия."
            },
            "voting_start": {
                "title": "Время выбора",
                "summary": "Начинается голосование.",
                "narration": "Время разговоров прошло. Теперь городу предстоит сделать тяжелый выбор и решить, кто виновен."
            },
            "lynch_victim": {
                "title": "Приговор толпы",
                "summary": f"Дневным голосованием был казнен игрок {victim}.",
                "narration": f"По итогам дневного голосования, гнев толпы обрушился на {victim}. Его судьба решена."
            },
            "lynch_tie": {
                "title": "Ничья",
                "summary": "Голоса разделились.",
                "narration": "Мнения разделились поровну. Сегодня никто не будет казнен, и напряжение в городе только растет."
            },
            "joke_voting_start": {
                "title": "Первые подозрения",
                "summary": "Кто кажется вам самым подозрительным?",
                "narration": "Пришло время поделиться первыми впечатлениями. Выберите того, кто кажется вам наиболее подозрительным."
            },
            "joke_vote_result": {
                "title": "Подозрительный тип",
                "summary": f"Самым подозрительным назвали игрока {victim}.",
                "narration": f"Большинство косо смотрит на игрока {victim}. Пока это ничего не значит, но осадок остался."
            },
            "joke_vote_tie": {
                "title": "Смешанные чувства",
                "summary": "Мнения о подозрительности разделились.",
                "narration": "Горожане не смогли определиться, кто выглядит подозрительнее всех. Кажется, никому нельзя доверять."
            },
            "game_over": {
                "title": "Финал",
                "summary": f"Игра завершена. Победители: {winner}.",
                "narration": "История этого города подошла к концу. Улицы опустели, и лишь ветер разносит эхо прошедших событий."
            }
        }

        template = base_templates.get(event_type, {
            "title": "Событие",
            "summary": "Произошло игровое событие.",
            "narration": "Ведущий подводит итоги..."
        })


        extra_narrative_parts = []
        whore_target = event_data.get('whore_target_name')
        if whore_target and event_type in ["night_kill", "night_save", "night_no_kill"]:
            extra_narrative_parts.append(
                f" Кроме того, {whore_target} провел ночь в очень приятной, но отвлекающей компании."
            )
        final_narration_text = template["narration"] + "".join(extra_narrative_parts)
        
        return AINarration(
            title=template["title"],
            summary=template["summary"],
            narration=final_narration_text
        )

ai_narrator = AINarrator()