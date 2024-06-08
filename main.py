import requests
import sys
from lxml import html
import re
from time import sleep


CHAT_IDS = ["6322851361", "6815733629"]
LIST_IDS = ["pLmKZJKw"]
BOT_TOKEN = "7251666204:AAFX-qCa-3FF2JPa5TkQ6l_EOxz52dD0JT4"
BOT_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
MSG_NO_FULL = "TestFlight slots for <b>{}</b> beta are now available! \
<a href='{}'>Download now</a>"
MSG_FULL = "<b>{}</b> beta program on TestFlight is now full"


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