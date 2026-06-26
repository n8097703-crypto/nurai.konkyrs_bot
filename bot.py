import os
import sys
import json
import logging
import re
from telebot import TeleBot, types

# Настройка логирования по требованиям конкурса
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

class PortfolioBot:
    def __init__(self):
        # 🔑 ВСТАВЬ СВОЙ ТОКЕН СЮДА (ВНУТРЬ КАВЫЧЕК):
        self.token = "8780561569:AAEDy5KlsiktXEwGhzjcL6_uhHGeNxRHwZU"
        
        # Проверка, если токен передается через сервер Render или командную строку
        if len(sys.argv) > 1 and sys.argv[1] != "debug" and not sys.argv[1].startswith("-"):
            self.token = sys.argv[1]
            
        if len(sys.argv) > 2 and sys.argv[2] == "debug":
            logging.getLogger().setLevel(logging.DEBUG)
            
        if not self.token or "ВСТАВЬ" in self.token:
            logging.critical("Критическая ошибка: Токен бота отсутствует в коде!")
            sys.exit(1)
            
        self.bot = TeleBot(self.token, parse_mode="Markdown")
        self.user_states = {} 
        self.config = self.load_json("data/config.json")
        self.content = self.load_json("data/content.json")
        self.register_handlers()

    def load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки JSON файла {path}: {e}")
            return {}

    def get_main_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btns = self.content.get("main_menu", {}).get("buttons", {})
        markup.add(
            types.KeyboardButton(btns.get("about", "👤 Обо мне")),
            types.KeyboardButton(btns.get("target", "🎯 Моя цель")),
            types.KeyboardButton(btns.get("way", "💻 Как я пришла в IT")),
            types.KeyboardButton(btns.get("mentor", "👨‍🏫 Мой ментор")),
            types.KeyboardButton(btns.get("progress", "📈 Мой прогресс")),
            types.KeyboardButton(btns.get("works", "🛠 Лучшие работы")),
            types.KeyboardButton(btns.get("hobbies", "🎸 Хобби")),
            types.KeyboardButton(btns.get("future", "🚀 Путь в будущее")),
            types.KeyboardButton(btns.get("quiz", "🏆 Викторина")),
            types.KeyboardButton(btns.get("ask_ai", "🤖 Спросить ИИ")),
            types.KeyboardButton(btns.get("links", "🔗 Ссылки"))
        )
        return markup

    def get_inline_back(self, target="main"):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="⬅️ Назад на Главную", callback_data=f"back_{target}"))
        return markup

    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            try:
                self.user_states[message.chat.id] = {"state": "main"}
                text = self.content.get("main_menu", {}).get("welcome", "👋 Добро пожаловать!")
                self.bot.send_message(message.chat.id, text, reply_markup=self.get_main_keyboard())
            except Exception as e:
                logging.error(f"Ошибка в команде start: {e}")

        @self.bot.message_handler(content_types=['text'])
        def handle_text_menu(message):
            chat_id = message.chat.id
            text = message.text
            btns = self.content.get("main_menu", {}).get("buttons", {})
            blocks = self.content.get("blocks", {})

            try:
                if self.user_states.get(chat_id, {}).get("state") == "ai_asking":
                    self.process_ai_search(chat_id, text)
                    return

                if text == btns.get("about"):
                    self.bot.send_message(chat_id, blocks.get("about", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("target"):
                    self.bot.send_message(chat_id, blocks.get("target", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("way"):
                    self.bot.send_message(chat_id, blocks.get("way", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("mentor"):
                    self.bot.send_message(chat_id, blocks.get("mentor", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("progress"):
                    self.bot.send_message(chat_id, blocks.get("progress", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("hobbies"):
                    self.bot.send_message(chat_id, blocks.get("hobbies", "Информация загружается..."), reply_markup=self.get_inline_back())
                elif text == btns.get("links"):
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("🐙 Открыть GitHub", url=self.config.get("GITHUB_URL", "https://github.com/n8097703-crypto/nurai.konkyrs_bot.git")))
                    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
                    self.bot.send_message(chat_id, blocks.get("links", "Ссылки..."), reply_markup=markup)
                elif text == btns.get("works"):
                    self.send_portfolio_works(chat_id)
                elif text == btns.get("future"):
                    self.start_future_quest(chat_id)
                elif text == btns.get("quiz"):
                    self.start_quiz(chat_id)
                elif text == btns.get("ask_ai"):
                    self.user_states[chat_id] = {"state": "ai_asking"}
                    self.bot.send_message(chat_id, "🤖 Режим ИИ-ассистента активен. Задайте любой вопрос про Нурай:")
                else:
                    if re.search(r"(привет|здравствуй|hello|hi)", text, re.IGNORECASE):
                        self.bot.send_message(chat_id, "👋 Привет! Рада видеть тебя в моем боте.")
                    else:
                        self.bot.send_message(chat_id, "💡 Выберите пункт меню или воспользуйтесь кнопкой *🤖 Спросить ИИ*.", reply_markup=self.get_main_keyboard())
            except Exception as e:
                logging.error(f"Ошибка обработки текстового ввода {text}: {e}")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callbacks(call):
            try:
                chat_id = call.message.chat.id
                data = call.data

                if data == "back_main":
                    self.user_states[chat_id] = {"state": "main"}
                    text = self.content.get("main_menu", {}).get("welcome", "👋 Добро пожаловать!")
                    self.bot.send_message(chat_id, text, reply_markup=self.get_main_keyboard())
                    self.bot.delete_message(chat_id, call.message.message_id)
                    return

                if data.startswith("quest_"):
                    next_step = data.split("_")[1]
                    self.continue_future_quest(chat_id, call.message.message_id, next_step)
                    return

                if data.startswith("quiz_"):
                    ans_data = data.split("_")
                    is_correct = ans_data[1] == "yes"
                    self.continue_quiz(chat_id, call.message.message_id, is_correct)
                    return

            except Exception as e:
                logging.error(f"Ошибка Callback-обработки: {e}")

    def send_portfolio_works(self, chat_id):
        works = self.content.get("works", {})
        if not works:
            self.bot.send_message(chat_id, "📁 Работы находятся на стадии загрузки.")
            return
        for key, work in works.items():
            caption = f"*{work['title']}*\n\n{work['description']}"
            img_path = work["image"]
            if os.path.exists(img_path):
                try:
                    with open(img_path, "rb") as photo:
                        self.bot.send_photo(chat_id, photo, caption=caption, parse_mode="Markdown")
                except Exception as e:
                    self.bot.send_message(chat_id, caption)
            else:
                self.bot.send_message(chat_id, caption)

    def start_future_quest(self, chat_id):
        self.user_states[chat_id] = {"state": "quest", "step": "step_1"}
        quest_data = self.content.get("quest", {}).get("steps", {}).get("step_1", {})
        if not quest_data:
            self.bot.send_message(chat_id, "🚀 Квест скоро начнется.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for opt in quest_data["options"]:
            markup.add(types.InlineKeyboardButton(opt["text"], callback_data=f"quest_{opt['next']}"))
        self.bot.send_message(chat_id, f"🔮 *Мини-квест:* {quest_data['text']}", reply_markup=markup)

    def continue_future_quest(self, chat_id, message_id, next_step):
        quest = self.content.get("quest", {})
        if next_step in quest.get("endings", {}):
            end_text = quest["endings"][next_step]
            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"🏁 *Квест завершен!*\n\n{end_text}")
            self.user_states[chat_id] = {"state": "main"}
            return
        step_data = quest.get("steps", {}).get(next_step)
        if step_data:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for opt in step_data["options"]:
                markup.add(types.InlineKeyboardButton(opt["text"], callback_data=f"quest_{opt['next']}"))
            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=step_data["text"], reply_markup=markup)

    def start_quiz(self, chat_id):
        self.user_states[chat_id] = {"state": "quiz", "current_q": 0, "score": 0}
        self.send_quiz_question(chat_id)

    def send_quiz_question(self, chat_id, message_id=None):
        user_data = self.user_states[chat_id]
        q_idx = user_data["current_q"]
        questions = self.content.get("quiz", {}).get("questions", [])
        
        if q_idx >= len(questions):
            score = user_data["score"]
            res_msg = self.content.get("quiz", {}).get("results", {}).get(str(score), "Молодец!")
            card = f"🏆 *Результат викторины*\n\nТвой результат: {score}/{len(questions)} правильных ответов.\n\n{res_msg}"
            if message_id:
                self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=card)
            else:
                self.bot.send_message(chat_id, card)
            self.user_states[chat_id] = {"state": "main"}
            return

        q_data = questions[q_idx]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ans in q_data["a"]:
            is_correct = "yes" if ans == q_data["correct"] else "no"
            markup.add(types.InlineKeyboardButton(ans, callback_data=f"quiz_{is_correct}"))

        text = f"❓ *Вопрос {q_idx+1}:* {q_data['q']}"
        if message_id:
            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        else:
            self.bot.send_message(chat_id, text, reply_markup=markup)

    def continue_quiz(self, chat_id, message_id, is_correct):
        if chat_id not in self.user_states or self.user_states[chat_id]["state"] != "quiz":
            return
        if is_correct:
            self.user_states[chat_id]["score"] += 1
        self.user_states[chat_id]["current_q"] += 1
        self.send_quiz_question(chat_id, message_id)

    def process_ai_search(self, chat_id, query):
        knowledge = self.content.get("ai_knowledge", [])
        matched_facts = []
        keywords_map = {
            r"(сколько лет|возраст|года|нурай)": [0],
            r"(гитар|музык|играет)": [1],
            r"(олимпиада|научн|место|конкурс|информатик)": [2],
            r"(цел|мечта|маме|будущее|дом|мотоцикл|автомобиль)": [3],
            r"(учитель|как пришла|школа|ниш|cap education|почему)": [4],
            r"(ментор|адиль|әділ|наставник)": [5],
            r"(проекты|создала|сделала|написала|dino|банкомат|калькулятор)": [6],
            r"(хобби|увлечения|лего|lego|кулинария|книги|пк|железо)": [7]
        }
        for regex, indices in keywords_map.items():
            if re.search(regex, query, re.IGNORECASE):
                for idx in indices:
                    if idx < len(knowledge) and knowledge[idx] not in matched_facts:
                        matched_facts.append(knowledge[idx])
        if matched_facts:
            facts_text = "\n• ".join(matched_facts)
            response = f"🤖 *ИИ-Помощник:*\n\nНайдено в базе знаний:\n\n• {facts_text}"
        else:
            response = "🤖 *ИИ-Помощник:*\n\nВ локальной базе знаний нет точного ответа. Спросите о целях, хобби или проектах Нурай."
        self.bot.send_message(chat_id, response, reply_markup=self.get_main_keyboard())
        self.user_states[chat_id] = {"state": "main"}

    def run(self):
        logging.info("Архитектурный бот-портфолио успешно запущен локально.")
        self.bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    portfolio_bot = PortfolioBot()
    portfolio_bot.run()
