from pytube import YouTube
from pytube import helpers

import os
import argparse
import json
import atexit

current_download = None

def clean_download():
    global current_download
    print("Cleaning up..")
    if not current_download is None:
        print("Cleaning up file: " + current_download)
        os.remove(current_downloa)

def main():
    parser = argparse.ArgumentParser(description="Download songs from YouTube")
    parser.add_argument("url", metavar='URL', type=str, nargs='?', help="YouTube URL")
    parser.add_argument("--output", metavar='Output', help="File name", type=str)

    args = parser.parse_args()

    song_name = args.output
    if song_name is None:
        song_name = "Song"
    download_song(YouTube(args.url, False, download_progress, download_complete), song_name)

def download_song(yt, name):

    global current_download
    
    stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('resolution').desc().first()
    if not stream is None:
        print("Downloading " + yt.watch_url)

        filename = helpers.safe_filename(name)
        
        stream.subtype = "m4a"
        file_target = '{filename}.{file_type}'.format(filename=filename, file_type=stream.subtype)

        if os.path.isfile(file_target):
            print("File already detected")
            return

        current_download = file_target

        stream.download(filename=filename)
        print("Download completed")
        return True
    else:
        print("Unable to download " + yt.watch_url)
        return False

def download_complete(stream, file):
    print("Downloaded " + file.name)

def download_progress(stream, chunk, file_handle, bytes_remaining):
    percentage = (float(stream.filesize - bytes_remaining) / float(stream.filesize))
    print "Progress: {0:.0f}%\r".format(percentage * 100),
    pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clean_download()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    