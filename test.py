import mutagen

src = "./rec_yt/202008300100 オードリーのオールナイトニッポン.m4a"
ft = mutagen.File(src)
ft["\xa9ART"] = u"オードリー"
ft["\xa9alb"] = u"オードリーのオールナイトニッポン"
ft.save()
print(ft.pprint())