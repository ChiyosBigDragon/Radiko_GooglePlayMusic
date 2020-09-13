import re
import requests
from bs4 import BeautifulSoup
import os
import shutil
import base64

def auth1():
    url = "https://radiko.jp/v2/api/auth1"
    res = requests.get(url, headers={"X-Radiko-App": "pc_html5", "X-Radiko-App-Version": "0.0.1", "X-Radiko-Device": "pc", "X-Radiko-User": "dummy_user"})
    return {"token": res.headers["X-Radiko-AuthToken"], "length": res.headers["X-Radiko-KeyLength"], "offset": res.headers["X-Radiko-KeyOffset"]}

def auth2(token, length, offset):
    url = "https://radiko.jp/v2/api/auth2"
    AUTH = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    key = base64.b64encode(AUTH[offset:(offset+length)].encode('utf-8'))
    res = requests.get(url, headers={"X-Radiko-AuthToken": token, "X-Radiko-PartialKey": key, "X-Radiko-Device": "pc", "X-Radiko-User": "dummy_user"})

def scrape(url, token):
    url = "http://radiko.jp/#!/ts/TBS/20200912000000"
    # url += '.html'
    # res = requests.get(url)
    res = requests.get(url, headers={"X-Radiko-Authtoken": token, "X-Radiko-App": "pc_html5", "X-Radiko-App-Version": "0.0.1", "X-Radiko-Device": "pc", "X-Radiko-User": "dummy_user"})
    print(res.headers)
    content = res.content
    soup = BeautifulSoup(content, "html.parser")
    print(soup)
    # <h1 class="live-detail__title">マイナビ Laughter Night</h1>
    # title = soup.find("h1", class_="live-detail__title").text
    title = soup.find("span", class_="area").text
    print(title)
    # pages = soup.find_all(class_='live-detail__title')
    # for page in pages :
    #     div = page.find(class_='entryBody')
    #     # 日付取得
    #     date = ''.join(div.find('h3').text.split())
    #     print(date)
    #     dir = './data/' + date + '/'
    #     os.mkdir(dir)
    #     # 詳細取得
    #     details = div.find('p').text
    #     with open(dir + str('details.txt'), 'w', encoding='utf-8') as file :
    #         file.write(details)
    #     # 画像取得
    #     imgs = page.find_all('img')
    #     cnt = 0
    #     for img in imgs :
    #         src = requests.get(img['src'])
    #         with open(dir + str(cnt).zfill(3) + str('.jpg'), 'wb') as file :
    #             file.write(src.content)
    #             cnt += 1

if __name__ == '__main__' :
    headers = auth1()
    auth2(headers["token"], int(headers["length"]), int(headers["offset"]))
    scrape("aaa", headers["token"])