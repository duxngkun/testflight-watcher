import requests
import sys
from lxml import html
import re
from time import sleep


CHAT_IDS = ["idtele1", "idtele2"]
LIST_IDS = ["idtf1", "idtf2"]
BOT_TOKEN = "token bot here!"
BOT_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
MSG_NO_FULL = "Nhóc, <b>{}</b> hiện đã mở thêm slot!\n\n<a href='{}'>Truy Cập Nhanh</a>"
MSG_FULL = "<b>{}</b> hiện đã đầy!"


def send_notification(tf_id, free_slots, title):
    dl_url = TESTFLIGHT_URL.format(tf_id)
    if free_slots:
        message = MSG_NO_FULL.format(title, dl_url)
    else:
        message = MSG_FULL.format(title)
    for chat_id in CHAT_IDS:
        requests.get(BOT_URL,
                     params={
                         "chat_id": chat_id,
                         "text": message,
                         "parse_mode": "html",
                         "disable_web_page_preview": "true"
                     })

XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
TESTFLIGHT_URL = 'https://testflight.apple.com/join/{}'
FULL_TEXTS = ['This beta is full.',
              "This beta isn't accepting any new testers right now."]

def watch(watch_ids, callback, notify_full=True, sleep_time=900):
    data = {}
    while True:
        for tf_id in watch_ids:
            req = requests.get(
                TESTFLIGHT_URL.format(tf_id),
                headers={"Accept-Language": "en-us"})
            page = html.fromstring(req.text)
            free_slots = page.xpath(XPATH_STATUS)[0] not in FULL_TEXTS

            if (tf_id not in data or data[tf_id] != free_slots):
                if free_slots or notify_full:
                    title = re.findall(
                        TITLE_REGEX,
                        page.xpath(XPATH_TITLE)[0])[0]
                    callback(tf_id, free_slots, title)
                data[tf_id] = free_slots
        sleep(sleep_time)

watch(LIST_IDS, send_notification)