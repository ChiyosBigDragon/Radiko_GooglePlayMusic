# coding:utf-8
import sys
import os
import shutil
import json
import subprocess
import argparse
from ytmusicapi import YTMusic
import mutagen

CACHE = "./cache_yt.json"
PROGRAM = "./program_yt.json"
RECORD_DIR = "./rec_yt/"

def upload(ytmusic, file, cache, program):
    # アップロード
    print("[upload] " + file, file=sys.stderr)
    # ID取得
    ytmusic.upload_song(file)
    # アップロード成功
    print("[done] " + file, file=sys.stderr)

# タグつけると壊れるので保留
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

def record(ytmusic, obj, cache, program):
    # 日付取得
    date = subprocess.check_output(["date", "+%Y%m%d", "-d", "next " + obj["day"]], universal_newlines=True).strip()
    date = subprocess.check_output(["date", "+%Y%m%d", "-d", "7 days ago " + date], universal_newlines=True).strip()
    start = date + obj["start"]
    end = date + obj["end"]
    title = start + " " + obj["title"]
    # キャッシュ作成
    if not (obj["title"] in cache):
        cache[obj["title"]] = list()
    # キャッシュヒット
    if date in cache[obj["title"]]:
        print("[skip] " + title, file=sys.stderr)
        return
    # 録音
    print("[rec] " + title, file=sys.stderr)
    if 1 == subprocess.run(["./rec_radiko_ts.sh", "-s", obj["station"], "-f", start, "-t", end, "-o", RECORD_DIR + title]):
        print("[error] " + title, file=sys.stderr)
        return
    print("[done] " + title, file=sys.stderr)
    # タグ編集
    setID3(file=RECORD_DIR+title+".m4a", artist=obj["artist"], album=obj["title"], artwork=obj["artwork"])
    # アップロード
    upload(ytmusic=ytmusic, program=program[obj["title"]], file=RECORD_DIR+title+".m4a", cache=cache)
    # キャッシュ書き込み
    cache[obj["title"]].append(date)

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
    print("[done]", file=sys.stderr)
    return ytmusic
    
def get_option():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-r", "--remove", action="store_true",
                           help="Remove record file")
    return argparser.parse_args()

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
    print("[done]", file=sys.stderr)
    
    # 録音
    for key in program:
        record(ytmusic, program[key], cache, program)

    print("[save] information", file=sys.stderr)
    # キャッシュ書き込み
    with open(CACHE, "w") as f:
        json.dump(cache, f)
    # 番組情報書き込み
    with open(PROGRAM, "w") as f:
        json.dump(program, f, indent=4, ensure_ascii=False)
    print("[done]", file=sys.stderr)

    # ファイル削除
    if args.remove:
        shutil.rmtree(RECORD_DIR)
        os.mkdir(RECORD_DIR)

    print("Exit")
    
