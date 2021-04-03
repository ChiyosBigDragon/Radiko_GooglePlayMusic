import yt
import shutil
import sys
import os
import shutil
import json
import subprocess
import argparse
import mutagen
import re
import requests
from bs4 import BeautifulSoup
import glob

ARTWORK_DIR = "./artwork/"

def scrape(station, date, date_start):
    url = f"http://radiko.jp/v3/program/station/date/{date}/{station}.xml"
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

if __name__ == "__main__":
    ytmusic = yt.login()
    l = glob.glob('rec_yt/202006190100 JUNK*.m4a')
    l.sort()
    # station = "LFR"
    for path in l:
        print(path)
        # date = path[4:12]
        # date = subprocess.check_output(["date", "+%Y%m%d", "-d", "1day ago " + date], universal_newlines=True).strip()
        # date_start = path[4:16]
        # title, date_end, pfm, img_path = scrape(station, date, date_start)
        # yt.setID3(path, pfm, title, img_path)
        # date_title = f"{date_start} {title}"
        # new_path = "./rec_yt/" + date_title + ".m4a"
        # print(new_path)
        # shutil.move(path, new_path)
        # yt.upload(ytmusic=ytmusic, file=new_path)
        yt.upload(ytmusic=ytmusic, file=path)
    print(len(l))
