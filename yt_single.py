# coding:utf-8
import sys
import os
import shutil
import json
import subprocess
import argparse
from ytmusicapi import YTMusic
import mutagen
import re
import requests
from bs4 import BeautifulSoup
import base64

CACHE = "./cache_yt.json"
PROGRAM = "./program_yt_single.json"
RECORD_DIR = "./rec_yt/"
ARTWORK_DIR = "./artwork/"

def scrape(station, date_start):
    url = f"http://radiko.jp/v3/program/station/weekly/{station}.xml"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "xml")
    page = soup.find("prog", ft=f"{date_start}00")
    date_end = page.get("to")
    title = page.find("title").text
    pfm = page.find("pfm").text
    img = page.find('img').text
    _root, ext = os.path.splitext(img)
    path = ARTWORK_DIR + f"{date_start} {title}" + ext
    src = requests.get(img)
    with open(path, 'wb') as file :
        file.write(src.content)
    return title, date_end[0:12], pfm, path

def upload(ytmusic, file):
    # アップロード
    print("[upload] " + file, file=sys.stderr)
    # ID取得
    ytmusic.upload_song(file)
    # アップロード成功
    print("[done] " + file, file=sys.stderr)

def setID3(file, artist=None, album=None, artwork=None):
    f = mutagen.File(file)
    if artist is not None:
        f["\xa9ART"] = artist
    if album is not None:
        f["\xa9alb"] = album
    if artwork is not None:
        _root, ext = os.path.splitext(artwork)
        if ext == ".png":
            with open(artwork, "rb") as img:
                f["covr"] = [mutagen.mp4.MP4Cover(img.read(), imageformat=mutagen.mp4.MP4Cover.FORMAT_PNG)]
        if ext == ".jpg":
            with open(artwork, "rb") as img:
                f["covr"] = [mutagen.mp4.MP4Cover(img.read(), imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG)]
    f.save()

def record(ytmusic, station, date, start):
    # 日付取得
    date_start = date + start
    title, date_end, pfm, img_path = scrape(station, date_start)
    date_title = f"{date_start} {title}"
    # キャッシュ作成
    if not (title in cache):
        cache[title] = list()
    # キャッシュヒット
    if date in cache[title]:
        print(f"[skip] {date_title}", file=sys.stderr)
        return
    # 録音
    print(f"[rec] {date_title}", file=sys.stderr)
    if 1 == subprocess.run(["./rec_radiko_ts.sh", "-s", station, "-f", date_start, "-t", date_end, "-o", RECORD_DIR + date_title]):
        print(f"[error] {date_title}", file=sys.stderr)
        return
    print(f"[done] {date_title}", file=sys.stderr)
    file_path = RECORD_DIR + date_title + ".m4a"
    # タグ編集
    setID3(file=file_path, artist=pfm, album=title, artwork=img_path)
    # アップロード
    upload(ytmusic=ytmusic, file=file_path)
    # キャッシュ書き込み
    cache[title].append(date)


def first_init():
    # 初回のみ認証
    # YTMusic.setup(filepath="headers_auth.json")
    # 録音ディレクトリ作成
    if not os.path.exists(RECORD_DIR):
        os.makedirs(RECORD_DIR)
    # キャッシュ作成
    if not os.path.exists(CACHE):
        with open(CACHE, "w") as f:
            json.dump({}, f, indent=4)
    # 番組情報作成
    if not os.path.exists(PROGRAM):
        with open(PROGRAM, "w") as f:
            program = {
                "オードリーのオールナイトニッポン": {
                    "title": "オードリーのオールナイトニッポン",
                    "day": "sunday",
                    "station": "LFR",
                    "start": "0100",
                    "end": "0300",
                    "artist": "オードリー(若林正恭/春日俊彰)",
                    "artwork": "./artwork/audrey.png"
                },
                "JUNK 伊集院光・深夜の馬鹿力": {
                    "title": "JUNK 伊集院光・深夜の馬鹿力",
                    "day": "tuesday",
                    "station": "TBS",
                    "start": "0100",
                    "end": "0300",
                    "artist": "伊集院光",
                    "artwork": "./artwork/baka.png"
                }
            }
            json.dump(program, f, indent=4, ensure_ascii=False)
        print("[create] " + PROGRAM, file=sys.stderr)
        print("Please fix it if necessary.", file=sys.stderr)
        print("Exit.", file=sys.stderr)
        sys.exit(0)

def login():
    # ログイン
    print("[login] Youtube Music", file=sys.stderr)
    ytmusic = YTMusic("headers_auth.json")
    return ytmusic
    
def get_option():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-r", "--remove", action="store_true",
                           help="Remove record file")
    return argparser.parse_args()

def weekly(ytmusic, station, day, start):
    # 日付取得
    date = subprocess.check_output(["date", "+%Y%m%d", "-d", "next " + day], universal_newlines=True).strip()
    date = subprocess.check_output(["date", "+%Y%m%d", "-d", "7 days ago " + date], universal_newlines=True).strip()
    date_start = date + start
    title, date_end, pfm, img_path = scrape(station, date_start)
    date_title = f"{date_start} {title}"
    # キャッシュ作成
    if not (title in cache):
        cache[title] = list()
    # キャッシュヒット
    if date in cache[title]:
        print(f"[skip] {date_title}", file=sys.stderr)
        return
    # 録音
    print(f"[rec] {date_title}", file=sys.stderr)
    if 1 == subprocess.run(["./rec_radiko_ts.sh", "-s", station, "-f", date_start, "-t", date_end, "-o", RECORD_DIR + date_title]):
        print(f"[error] {date_title}", file=sys.stderr)
        return
    print(f"[done] {date_title}", file=sys.stderr)
    file_path = RECORD_DIR + date_title + ".m4a"
    # タグ編集
    setID3(file=file_path, artist=pfm, album=title, artwork=img_path)
    # アップロード
    upload(ytmusic=ytmusic, file=file_path)
    # キャッシュ書き込み
    cache[title].append(date)

if __name__ == "__main__":
    # 引数設定
    args = get_option()
    # 初期化
    first_init()
    # ログイン
    ytmusic = login()
    # キャッシュ読み込み
    print("[load] information", file=sys.stderr)
    cache = None
    with open(CACHE, "r") as f:
        cache = json.load(f)
    # 番組情報読み込み
    program = None
    with open(PROGRAM, "r") as f:
        program = json.load(f)
    
    # 録音
    for key in program:
        record(ytmusic, program[key]["station"], program[key]["date"], program[key]["start"])

    print("[save] information", file=sys.stderr)
    # キャッシュ書き込み
    with open(CACHE, "w") as f:
        json.dump(cache, f)
    # 番組情報書き込み
    with open(PROGRAM, "w") as f:
        json.dump(program, f, indent=4, ensure_ascii=False)

    # ファイル削除
    if args.remove:
        shutil.rmtree(RECORD_DIR)
        os.mkdir(RECORD_DIR)

    print("Exit")
    
