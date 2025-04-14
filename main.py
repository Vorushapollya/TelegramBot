import os
import logging
import tempfile
import cv2
import telebot
from telebot import types
from utils import SLInference




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SignLanguageBot:
    def __init__(self, token, config_path):
        self.bot = telebot.TeleBot(token)
        self.config_path = config_path
        self.processor = SLInference(config_path)
        self.processor.start()
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def start_message(message):
            self.show_main_menu(message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callbacks(call):
            try:
                if call.data == "perevod":
                    self.handle_translation(call)
                elif call.data == "education":
                    self.show_education_menu(call)
                elif call.data == "edu_fraze":
                    self.show_phrases_page1(call, call.message.chat.id)
                elif call.data == "end_z":
                    self.show_main_menu(call.message.chat.id, call.message.message_id)
                elif call.data == "end_n":
                    self.show_education_menu(call)
                elif call.data == "edu_fraze3":
                    self.show_phrases_page3(call, call.message.chat.id)
                elif call.data == 'edu_fraze2':
                    self.show_phrases_page2(call, call.message.chat.id)
                elif call.data == "end_nn":
                    self.show_phrases_page1(call)

            except Exception as e:
                logger.error(f"Callback error: {str(e)}")
                self.bot.answer_callback_query(call.id, "❌ Произошла ошибка при обработке запроса")

        @self.bot.message_handler(content_types=['video'])
        def handle_video(message):
            try:
                self.bot.send_chat_action(message.chat.id, 'typing')

                # Скачивание и обработка видео
                file_info = self.bot.get_file(message.video.file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)

                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
                    tmp_file.write(downloaded_file)
                    video_path = tmp_file.name

                predictions = self.process_video(video_path)
                response = self.format_response(predictions)

                # Отправка результата
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ В ГЛАВНОЕ МЕНЮ", callback_data="end_z"))
                self.bot.reply_to(message, response, reply_markup=markup)

            except Exception as e:
                logger.error(f"Error: {str(e)}")
                self.bot.reply_to(message, "❌ Ошибка обработки видео")
            finally:
                if 'tmp_file' in locals():
                    os.remove(video_path)

    def show_main_menu(self, chat_id, message_id=None):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Обнаружить Дипфейк🤖", callback_data="perevod")
        btn2 = types.InlineKeyboardButton("Обучение. Что такое дипфейки?🧠", callback_data="education")
        markup.add(btn1, btn2)
        text= "Добро пожаловать!👋\nЭто бот для автоматического распознавания неестественных движений глаз и мимики в дипфейках \n👇Выбери команду снизу и я помогу тебе!👇"
        self.bot.send_photo(chat_id, photo=open('welcome.jpg', 'rb'))



        if message_id:
            self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=markup
            )
        else:
            self.bot.send_message(chat_id, text, reply_markup=markup)

    def handle_translation(self, call):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ ВЫХОД", callback_data="end_z"))

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🇷🇺 Отправь мне видео с возможным дипфейком (до 1 минуты)\nЯ постараюсь понять дипфейк это или нет!",
            reply_markup=markup
        )

    def show_education_menu(self, call):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Что такое Дипфейки?📖", callback_data="edu_fraze"),
            types.InlineKeyboardButton("Как распознать Дипфейки🔍", callback_data="edu_fraze2"),
            types.InlineKeyboardButton("Какие типы Дипфейков бывают🤖", callback_data="edu_fraze3"),
            types.InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="end_z")
        )

        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выбери с чего хочешь начать",
            reply_markup=markup
        )

    def create_phrases_markup(self, page):
        markup = types.InlineKeyboardMarkup()

        if page == 1:
            buttons = [
                ("⬅️ НАЗАД", "end_n"),
                (" НА ГЛАВНУЮ ➡️", "end_z")
            ]
        else:

            buttons = [
                ("⬅️ НАЗАД", "end_nn")
            ]

        # Добавляем основные кнопки
        #for i in range(0, len(buttons), 2):
            #row = [types.InlineKeyboardButton(text, url=url) for text, url in buttons[i:i + 2]]
            #markup.add(*row)

        # Добавляем кнопки навигации
        nav_row = [types.InlineKeyboardButton(text, callback_data=data) for text, data in buttons]
        markup.add(*nav_row)

        return markup

    def show_phrases_page2(self, call, chat_id):
        self.bot.send_video(chat_id, video=open('deepfakevideo2.mp4', "rb", ))
        self.bot.send_message(chat_id, text = 'Как распознать Дипфейки?🔍\nТехнология deepfake пока не так совершенна, чтобы обычный пользователь не смог ее заметить. Какие признаки помогут распознать глубокую подделку:\n1⃣ Объект двигается неровно\n2⃣ Голос плохо синхронизируется с движениями губ\n3⃣ У моделей может не совпадать цвет правого и левого глаза\n4⃣ Объект может вообще не моргать (или моргать странно)\n🎥Выше вы можете ознакомиться с видео о том, как распознать дипфейки',
            reply_markup=self.create_phrases_markup(1)
        )


    def show_phrases_page3(self, call, chat_id):
        self.bot.send_video(chat_id, video=open('deepfakevideo3.mp4', "rb"))
        self.bot.send_message(chat_id,text='Какие типы дипфейков бывают🧠\nПоначалу дипфейки не были особо популярны. О них знал только небольшой круг специалистов. Однако в 2009 году вышел фильм под названием «Аватар». Огромное количество зрителей увидели технологию в действии\n🎥Выше вы можете ознакомиться с видео о том, какие дипфейки встречаются в нашей жизни',
            reply_markup=self.create_phrases_markup(1)
        )

    def show_phrases_page1(self, call, chat_id):
        self.bot.send_video(chat_id, video=open('deepfakevideo1.mp4', "rb"))
        self.bot.send_message(chat_id, text='Что такое Дипфейки🤖\n❗Многие люди не знают, что такое дипфейк. Это слово было сформировано из двух выражений: deep learning («глубокое обучение» — термин, использующийся в сфере обучения искусственного интеллекта) и fake («подделка, фальшивка»). Таким образом, deepfake — это поддельные видео и фотографии, которые сделаны с использованием искусственного интеллекта. Проще говоря, лицо одного человека заменяется лицом другого\n🎥Выше вы можете ознакомиться с видео о том, что такое дипфейки',
            reply_markup=self.create_phrases_markup(1)
        )

    def process_video(self, video_path):
        predictions = []
        cap = cv2.VideoCapture(video_path)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (224, 224))
            self.processor.input_queue.append(frame)

            if self.processor.pred and self.processor.pred not in ['', 'no']:
                predictions.append(self.processor.pred)

        cap.release()
        return predictions

    def format_response(self, predictions):
        if not predictions:
            return "❌ Не удалось распознать дипфейк"

        unique_gestures = []
        for gesture in predictions:
            if not unique_gestures or gesture != unique_gestures[-1]:
                unique_gestures.append(gesture)

        return "В данном видео присутвует дипфейк🤖"

    def run(self):
        logger.info("Bot started")
        self.bot.infinity_polling()



if __name__ == "__main__":
    TOKEN = "7790245695:AAG7OaWij5LXfEaWO2VyJzjSV61DK77Lsro"
    CONFIG_PATH = os.path.join("configs", "config.json")

    bot = SignLanguageBot(TOKEN, CONFIG_PATH)
    bot.run()
