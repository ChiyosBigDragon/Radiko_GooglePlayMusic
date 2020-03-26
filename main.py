import sys
import os
import shutil
import json
import subprocess
from gmusicapi import Musicmanager, Mobileclient
import argparse

# from mutagen.easyid3 import EasyID3
# from mutagen.mp4 import MP4 # ID3, TIT2, TOPE, TALB, APIC, ID3NoHeaderError

MUSICMANAGER_CREDENTIAL = "./musicmanager.cred"
MOBILECLIENT_CREDENTIAL = "./mobileclient.cred"
CACHE = "./cache.json"
PROGRAM = "./program.json"
RECORD_DIR = "./rec/"
mobileclient_api = None
musicmanager_api = None

def upload(file, cache, program):
    # アップロード
    print("[upload] " + file, file=sys.stderr)
    (uploaded, matched, not_uploaded) = musicmanager_api.upload(file)
    # すでに存在？
    if matched:
        print("[skip] already uploaded: " + file, file=sys.stderr)
        return
    # エラー
    if not_uploaded:
        print("[error] could not upload: " + file, file=sys.stderr)
        return
    # アップロード成功
    print("[done] " + file, file=sys.stderr)
    # ID取得
    music_id = uploaded[file]
    # プレイリスト作成
    if not program.get("playlist"):
        print("[create] playlist: " + program["title"], file=sys.stderr)
        program["playlist"] = mobileclient_api.create_playlist(program["title"])
        print("[done] playlist: " + program["title"], file=sys.stderr)
    # プレイリスト追加
    print("[add] playlist: " + program["title"], file=sys.stderr)
    mobileclient_api.add_songs_to_playlist(program["playlist"], music_id)
    print("[done] playlist: " + program["title"], file=sys.stderr)

# タグつけると壊れるので保留
def setID3(title, artist=None, album=None, artwork=None):
    return
    # tags = MP4("./rec/" + title + ".m4a").tags
    # tags.pprint()
    # try:
    #     tag = ID3("./rec/" + title + ".m4a")
    # except ID3NoHeaderError:
    #     tag = ID3()
    # tag.add(TIT2(encoding=3, text=title))
    # if artist is not None:
    #     tag.add(TOPE(encoding=3, text=artist))
    # if album is not None:
    #     tag.add(TALB(encoding=3, text=album))
    # if artwork is not None:
    #     ext = os.path.splitext(artwork)[1][1:]
    #     mime = "image/" + ext
    #     with open(artwork, "r") as f:
    #         tag.add(APIC(encoding=3, mime=mime, type=TYPE_COVER_FRONT, data=f.read()))
    # print(tag.pprint())
    # tag.save("./rec/" + title + ".m4a")
    # tag = ID3()
    # tag.save("./rec/" + title + ".m4a")

def record(obj, cache, program):
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
    # setID3(title, artist=obj["artist"], album=obj["title"], artwork=obj["artwork"])
    # アップロード
    upload(program=program[obj["title"]], file=RECORD_DIR+title+".m4a", cache=cache)
    # キャッシュ書き込み
    cache[obj["title"]].append(date)

def first_init():
    # 初回のみ認証
    if not os.path.exists(MUSICMANAGER_CREDENTIAL):
        musicmanager_api.perform_oauth(MUSICMANAGER_CREDENTIAL)
    if not os.path.exists(MOBILECLIENT_CREDENTIAL):
        mobileclient_api.perform_oauth(MOBILECLIENT_CREDENTIAL)
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
    print("[login] Google Play Music", file=sys.stderr)
    mobileclient_api.oauth_login(Mobileclient.FROM_MAC_ADDRESS, MOBILECLIENT_CREDENTIAL)
    if not mobileclient_api.is_authenticated():
        print("[error] login failed", file=sys.stderr)
        exit(1)
    musicmanager_api.login(MUSICMANAGER_CREDENTIAL)
    if not musicmanager_api.is_authenticated():
        print("[error] login failed", file=sys.stderr)
        exit(1)
    print("[done]", file=sys.stderr)
    
def get_option():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-r", "--remove", action="store_true",
                           help="Remove record file")
    return argparser.parse_args()

if __name__ == "__main__":
    # 引数設定
    args = get_option()
    # Google Play Music API
    musicmanager_api = Musicmanager()
    mobileclient_api = Mobileclient()
    # 初期化
    first_init()
    # ログイン
    login()
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
        record(program[key], cache, program)

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
    
