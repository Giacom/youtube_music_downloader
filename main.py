
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
forced_type = None

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
    parser.add_argument("--amazon-start", metavar='Start', action='store', default=1, type=int)
    parser.add_argument("--amazon-end", metavar='End', action='store', default=500, type=int)
    parser.add_argument("--dry-run", action='store_true', help="Do not download the file")
    parser.add_argument("--force-type", metavar="Type", help="Force the file to be a file-type", type=str)
    parser.add_argument("--output", metavar='Output', help="Folder name", default="song_downloader", type=str)

    args = parser.parse_args()
    
    global youtube_search
    youtube_search = build("youtube", "v3")

    global dry_run
    dry_run = args.dry_run

    global forced_type
    forced_type = args.force_type

    global download_directory
    download_directory = args.output
    if not os.path.exists(download_directory):
        os.mkdir(download_directory)

    if not args.amazon_playlist_json is None:
        download_amazon_json(args.amazon_playlist_json, args.amazon_start, args.amazon_end)
    elif not args.song is None:
        get_song(args.category, args.song, args.artist)


def download_amazon_json(file, start, end):
    amazon_json = json.load(file)
    songs = amazon_json["playlists"][0]["tracks"]
    category = remove_non_ascii(amazon_json["playlists"][0]["metadata"]["title"])
    
    song_num = 0
    for song in songs:
        song_num += 1
        if song_num < start:
            continue
        if song_num > end:
            break
       

        metadata = song["metadata"]["requestedMetadata"]
        title = clean_title(remove_non_ascii(metadata["title"]))
        artist = remove_non_ascii(metadata["artistName"])
        album = remove_non_ascii(metadata["albumName"])
        
        print("Song {0}/{1}\nProcessing {2} - {3}".format(song_num, len(songs), title, artist))

        global dry_run
        if dry_run == False:
            target = download_directory
            if not category is None:
                target += "/" + category
            if not os.path.exists(target):
                os.mkdir(target)
            filename = helpers.safe_filename(title + " - " + artist)
        
            global forced_type
            file_type = "mp4"
            if not forced_type is None:
                file_type = forced_type
            file_target = '{filename}.{type}'.format(filename=filename, type=file_type)

            if os.path.isfile(target + "/" + file_target):
                print("File already detected")
                continue

        urls = search_song(title, artist)
        for url in urls:
            downloaded = download_song(YouTube(url, False, download_progress, download_complete), category, title, artist)
            if downloaded:
                break

        #print(clean_title(title) + " - " + title + " = " + artist + " / " + album)

def download_complete(stream, file):
    pass

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
    urls = search_song(song, artist)
    for url in urls:
        downloaded = download_song(YouTube(url), category, song, artist)
        if downloaded == True:
            break

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
        
        global forced_type
        if not forced_type is None:
            stream.subtype = forced_type
        file_target = '{filename}.{file_type}'.format(filename=filename, file_type=stream.subtype)

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
        return True
    else:
        print("Unable to download " + yt.watch_url)
        return False


def search_song(song, artist):
    global youtube_search

    max_results = 5

    print("Searching for " + song + " by " + artist)
    search_query = song + " " + artist + " song original"#+ " HQ song audio"
    result = youtube_search.search().list(q=search_query, part="id,snippet", maxResults=max_results).execute()

    urls = []

    for i in xrange(max_results):
        try:
            video_id = result["items"][i]["id"]["videoId"]

            if not video_id is None:
                url_to_download = "https://www.youtube.com/watch?v=" + video_id
                urls.append(url_to_download)

                title = remove_non_ascii(result["items"][i]["snippet"]["title"])

                print("Found {0}".format(title))
        except BaseException as e:
            print("Error searching for song: " + str(e))
            continue
    return urls


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