import requests
import os
from PIL import Image
from urllib.parse import quote_plus
import pytesseract
from bs4 import BeautifulSoup as bs
import time
from multiprocessing import Pool

N_PAGES = 10
URL_SEARCH = "https://{domain}/search?q={query}&btnG=Search&gbv=1"
DOMAIN = "www.google.com"
AXIS = {
    'chongding': {
        'q': (80, 348, 1000, 600),
        'a1': (130, 670, 950, 750),
        'a2': (130, 820, 950, 900),
        'a3': (130, 990, 950, 1070)
    },
    'xigua': {
        'q': (80, 400, 1000, 580),
        'a1': (130, 740, 950, 810),
        'a2': (130, 930, 950, 1000),
        'a3': (130, 1120, 950, 1190)
    }
}


def pull_screenshot():
    os.system("adb shell screencap -p /sdcard/autoDati/test.png")
    os.system("adb pull /sdcard/autoDati/test.png")


def read_text(website='chongding'):
    img = Image.open("test.png")

    area_qu = AXIS[website]["q"]
    qu_img = img.crop(area_qu)
    qu_img.show()
    ans_img = map(img.crop, (AXIS[website]["a1"], AXIS[website]["a2"], AXIS[website]["a3"]))

    pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"

    with Pool(4) as p:
        qu_result = p.apply_async(extract_text, args=(qu_img, False))
        ans_result = [p.apply_async(extract_text, args=(img, )) for img in ans_img]

        qu = qu_result.get()
        ans = [r.get() for r in ans_result]

    return qu, ans


def extract_text(img, is_sel=True):
    string = pytesseract.image_to_string(
        img, lang="chi_sim")

    if is_sel:
        string = string.replace(" ", "").split("/")[0]
    else:
        string = string.replace("\n", "").replace("_", "一")[2:]
    return string


def find_answear(q, sel, domain=DOMAIN, n_check_pages=N_PAGES):
    proxies = {
        'http': 'http://127.0.0.1:1087',
        'https': 'http://127.0.0.1:1087'
    }
    url = URL_SEARCH.format(
        domain=domain, query=quote_plus(q)
    )
    r = requests.get(url, proxies=proxies)
    soup = bs(r.text, "lxml")

    recall_s1, recall_s2, recall_s3 = 0, 0, 0
    s1, s2, s3 = sel
    for article in soup.find_all("span", class_="st")[:n_check_pages]:
        content = article.text

        if s1 in content:
            recall_s1 += 1
        if s2 in content:
            recall_s2 += 1
        if s3 in content:
            recall_s3 += 1
    print(recall_s1 / n_check_pages, recall_s2 / n_check_pages, recall_s3 / n_check_pages)

t1 = time.time()
pull_screenshot()
t2 = time.time()

question, selections = read_text("chongding")

print(question)
print(selections)

t3 = time.time()

find_answear(question, selections)
t4 = time.time()

print(t2 - t1, t3 - t2, t4 - t3)
