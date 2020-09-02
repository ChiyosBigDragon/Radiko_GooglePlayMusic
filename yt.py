from ytmusicapi import YTMusic
# YTMusic.setup(filepath="headers_auth.json")
ytmusic = YTMusic("headers_auth.json")

# print(ytmusic.create_playlist(title="aiueo", description="aaa"))

# print(ytmusic.get_library_upload_songs())
print(ytmusic.upload_song("./rec/202003210300 霜降り明星のオールナイトニッポン0(ZERO).m4a"))