import telebot
import os
import json
import requests
from lxml import html
import re
from time import sleep
import threading

BOT_TOKEN = "7451675333:AAHSQYV_NNA53mU3kHbcEH7a2MSKE49xiOU"  # Thay YOUR_BOT_TOKEN bằng token của bot của bạn
bot = telebot.TeleBot(BOT_TOKEN)
MSG_NO_FULL = "Nhóc, <b>{}</b> hiện đã mở thêm slot!\n\n<a href='{}'>Truy Cập Nhanh</a>"
MSG_FULL = "<b>{}</b> hiện đã đầy!"
USER_DATA_PATH = "user"

def send_notification(tf_id, free_slots, title, chat_id):
    dl_url = TESTFLIGHT_URL.format(tf_id)
    if free_slots:
        message = MSG_NO_FULL.format(title, dl_url)
    else:
        message = MSG_FULL.format(title)
    bot.send_message(chat_id, message, parse_mode="html")

XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
TESTFLIGHT_URL = 'https://testflight.apple.com/join/{}'
FULL_TEXTS = ['This beta is full.', "This beta isn't accepting any new testers right now."]

def watch(watch_ids, callback, chat_id, notify_full=True, sleep_time=1):
    data = {}
    while True:
        for tf_id in watch_ids:
            req = requests.get(
                TESTFLIGHT_URL.format(tf_id),
                headers={"Accept-Language": "en-us"})
            page = html.fromstring(req.text)
            status_elements = page.xpath(XPATH_STATUS)
            if not status_elements:
                print(f"Could not find status for TF ID: {tf_id}")
                continue
            free_slots = status_elements[0] not in FULL_TEXTS

            if (tf_id not in data or data[tf_id] != free_slots):
                if free_slots or notify_full:
                    title = re.findall(
                        TITLE_REGEX,
                        page.xpath(XPATH_TITLE)[0])[0]
                    callback(tf_id, free_slots, title, chat_id)
                data[tf_id] = free_slots
                print("Watched TF ID: {}, Free Slots: {}".format(tf_id, "Available" if free_slots else "Full"))
        sleep(sleep_time)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    user_file_path = os.path.join(USER_DATA_PATH, f"{chat_id}.json")
    if not os.path.exists(USER_DATA_PATH):
        os.makedirs(USER_DATA_PATH)
    if not os.path.exists(user_file_path):
        with open(user_file_path, "w") as file:
            json.dump([], file)
    bot.reply_to(message, "👋 Chào bạn! Tôi là một con 🤖 kiểm tra coi ID/URL Testflight Beta đang ✔️ or ❌.\n⚙ Hãy coi lệnh ở [Menu] góc trái bên dưới khung CHAT!", parse_mode="HTML")

@bot.message_handler(commands=['add'])
def add(message):
    chat_id = str(message.chat.id)
    user_file_path = os.path.join(USER_DATA_PATH, f"{chat_id}.json")
    bot.reply_to(message, "Gửi cho tôi ID/URL TestFlight bạn cần kiểm tra:")

    def handle_add_id(add_message):
        input_text = add_message.text.strip()
        if input_text.startswith("https://testflight.apple.com/join/"):
            match = re.match(r"https://testflight.apple.com/join/(\w+)", input_text)
            if match:
                tf_id = match.group(1)
            else:
                bot.reply_to(message, "URL không hợp lệ, nó phải có dạng: https://testflight.apple.com/join/XxXXx")
                return
        else:
            tf_id = input_text
        
        try:
            with open(user_file_path, "r") as file:
                list_ids = json.load(file)
        except json.JSONDecodeError:
            list_ids = []
        
        if tf_id in list_ids:
            bot.reply_to(message, f"ID '{tf_id}' đã tồn tại trong danh sách.")
        else:
            list_ids.append(tf_id)
            with open(user_file_path, "w") as file:
                json.dump(list_ids, file)
            bot.reply_to(message, f"Đã thêm ID: {tf_id}. Nếu muốn thêm tiếp hãy nhập lại lệnh!")
    
    bot.register_next_step_handler(message, handle_add_id)

@bot.message_handler(commands=['list'])
def list_ids(message):
    chat_id = str(message.chat.id)
    user_file_path = os.path.join(USER_DATA_PATH, f"{chat_id}.json")
    try:
        with open(user_file_path, "r") as file:
            list_ids = json.load(file)
        if list_ids:
            list_message = "Danh sách các ID TestFlight bạn đã thêm:\n"
            for idx, tf_id in enumerate(list_ids, start=1):
                list_message += f"{idx}. {tf_id}\n"
        else:
            list_message = "Bạn chưa thêm bất kỳ ID TestFlight nào."
    except (json.JSONDecodeError, FileNotFoundError):
        list_message = "Bạn chưa thêm bất kỳ ID TestFlight nào."
    bot.reply_to(message, list_message)

@bot.message_handler(commands=['delete'])
def delete(message):
    chat_id = str(message.chat.id)
    user_file_path = os.path.join(USER_DATA_PATH, f"{chat_id}.json")
    bot.reply_to(message, "Gửi cho tôi ID/URL TestFlight bạn muốn xoá:")

    def handle_delete_id(delete_message):
        input_text = delete_message.text.strip()
        if input_text.startswith("https://testflight.apple.com/join/"):
            match = re.match(r"https://testflight.apple.com/join/(\w+)", input_text)
            if match:
                tf_id = match.group(1)
            else:
                bot.reply_to(message, "URL không hợp lệ, nó phải có dạng: https://testflight.apple.com/join/XxXXx")
                return
        else:
            tf_id = input_text
        
        try:
            with open(user_file_path, "r") as file:
                list_ids = json.load(file)
        except json.JSONDecodeError:
            list_ids = []
        
        if tf_id in list_ids:
            list_ids.remove(tf_id)
            with open(user_file_path, "w") as file:
                json.dump(list_ids, file)
            bot.reply_to(message, f"Đã xoá ID: {tf_id} khỏi danh sách.")
        else:
            bot.reply_to(message, f"ID '{tf_id}' không tồn tại trong danh sách.")
    
    bot.register_next_step_handler(message, handle_delete_id)

@bot.message_handler(commands=['watcher'])
def watcher(message):
    chat_id = str(message.chat.id)
    user_file_path = os.path.join(USER_DATA_PATH, f"{chat_id}.json")
    try:
        with open(user_file_path, "r") as file:
            watch_ids = json.load(file)
        if watch_ids:
            bot.send_message(chat_id, "Bắt đầu tiến hành kiểm tra trạng thái ID TestFlight...")
            threading.Thread(target=watch, args=(watch_ids, send_notification, chat_id)).start()
        else:
            bot.send_message(chat_id, "Danh sách ID TestFlight đang trống. Hãy thêm ID trước khi theo dõi.")
    except (json.JSONDecodeError, FileNotFoundError):
        bot.send_message(chat_id, "Danh sách ID TestFlight đang trống. Hãy thêm ID trước khi theo dõi.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Không rõ yêu cầu của bạn. Hãy sử dụng các lệnh /start, /add, /list, /delete hoặc /watcher để tương tác với bot.")

def main():
    bot.polling()

if __name__ == "__main__":
    main()