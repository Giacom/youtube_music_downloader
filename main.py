
from pytube import YouTube
from pytube import helpers
from googleapiclient.discovery import build
from unidecode import unidecode

import os
import argparse
import json
import atexit

download_directory = "music_downloader"
youtube_search = None
current_download = None
dry_run = False

def clean_download():
    global current_download
    print("Cleaning up..")
    if not current_download is None:
        print("Cleaning up file: " + current_download)
        os.remove(current_download)

def main():
    parser = argparse.ArgumentParser(description="Download songs from YouTube")
    parser.add_argument("song", metavar='Song', type=str, nargs='?', help="Song name to download")
    parser.add_argument("artist", metavar='Artist', type=str, nargs='?', help="Artist name")
    parser.add_argument("category", metavar='Category', type=str, nargs='?', help="Song category for organisation")
    parser.add_argument("--amazon-playlist-json", metavar='JSON', type=file, help="Amazon playlist JSON file to go through and download from")
    parser.add_argument("--dry-run", action='store_true', help="Do not download the file")


    args = parser.parse_args()
    
    global youtube_search
    youtube_search = build("youtube", "v3")

    global dry_run
    dry_run = args.dry_run

    if not os.path.exists(download_directory):
        os.mkdir(download_directory)

    if not args.amazon_playlist_json is None:
        download_amazon_json(args.amazon_playlist_json)
    elif not args.song is None:
        get_song(args.category, args.song, args.artist)


def download_amazon_json(file):
    amazon_json = json.load(file)
    songs = amazon_json["playlists"][0]["tracks"]
    category = remove_non_ascii(amazon_json["playlists"][0]["metadata"]["title"])
    
    song_num = 0
    for song in songs:
        song_num += 1
        print("Song {0}/{1}".format(song_num, len(songs)))

        metadata = song["metadata"]["requestedMetadata"]
        title = clean_title(remove_non_ascii(metadata["title"]))
        artist = remove_non_ascii(metadata["artistName"])
        album = remove_non_ascii(metadata["albumName"])

        global dry_run
        if dry_run == False:
            target = download_directory
            if not category is None:
                target += "/" + category
            if not os.path.exists(target):
                os.mkdir(target)
            filename = helpers.safe_filename(title + " - " + artist)
        
            file_target = '{filename}.mp4'.format(filename=filename)

            if os.path.isfile(target + "/" + file_target):
                print("File already detected")
                continue

        url = search_song(title, artist)
        if not url is None:
            download_song(YouTube(url, False, download_progress, download_complete), category, title, artist)
        #print(clean_title(title) + " - " + title + " = " + artist + " / " + album)

def download_complete(stream, file):
    print("Downloaded " + file.name)

def download_progress(stream, chunk, file_handle, bytes_remaining):
    percentage = (float(stream.filesize - bytes_remaining) / float(stream.filesize))
    print "Progress: {0:.0f}%\r".format(percentage * 100),
    pass

def clean_title(title):
    end = len(title) + 1
    ignore_char = 0
    for c in reversed(title):
        end -= 1
        if c == ' ':
            continue
        if c == ')' or c == ']':
            ignore_char += 1
            continue
        if c == '(' or c == '[':
            ignore_char -= 1
            continue
        if ignore_char > 0:
            continue
        break
    return title[:end]


def get_song(category, song, artist):
    urlToDownload = search_song(song, artist)
    if not urlToDownload is None:
        download_song(YouTube(urlToDownload), category, song, artist)

def download_song(yt, category, song, artist):
    global dry_run
    if dry_run == True:
        return

    global current_download
    
    stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('resolution').desc().first()
    if not stream is None:
        print("Downloading " + yt.watch_url)

        target = download_directory
        if not category is None:
            target += "/" + category
        if not os.path.exists(target):
            os.mkdir(target)
        filename = helpers.safe_filename(song + " - " + artist)
        
        file_target = '{filename}.{s.subtype}'.format(filename=filename, s=stream)

        file_path = target + "/" + file_target
        if os.path.isfile(file_path):
            print("File already detected")
            return

        current_download = file_path

        # while os.path.isfile(target + "/" + file_target):
        #     filename += " (Copy)"
        #     file_target = '{filename}.{s.subtype}'.format(filename=filename, s=stream)

        stream.download(target, filename)
        print("Download completed")
    else:
        print("Unable to download " + yt.watch_url)


def search_song(song, artist):
    global youtube_search

    print("Searching for " + song + " by " + artist)
    search_query = song + " " + artist + " song"#+ " HQ song audio"
    result = youtube_search.search().list(q=search_query, part="id,snippet", maxResults=1).execute()

    videoId = None
    try:
        videoId = result["items"][0]["id"]["videoId"]
        print("Found {0}".format(result["items"][0]["snippet"]["title"]))
    except:
        print("Error searching for song")
        return None

    urlToDownload = "https://www.youtube.com/watch?v=" + videoId
    return urlToDownload

def remove_non_ascii(text):
    if isinstance(text, unicode):
        return unidecode(text)
    return text

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clean_download()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)