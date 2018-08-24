# youtube_music_downloader

Mainly made to be able to easily download songs that I had added from Amazon Music

```
Download songs from YouTube

positional arguments:
  Song                  Song name to download
  Artist                Artist name
  Category              Song category for organisation

optional arguments:
  -h, --help            show this help message and exit
  --amazon-playlist-json JSON
                        Amazon playlist JSON file to go through and download
                        from
  --dry-run             Do not download the file
```

You can download an Amazon Music Playlist JSON file (2018) with the optional argument.
To retrieve the JSON:

1. Open the Amazon Web Player
2. Right click anywhere
3. Go to the "Inspect Element" menu
4. Go to the network tab
5. Open the playlist you want to download
6. Look for a row of recorded data called "/??/api/circus/v3", there may be multiple
7. Look at the "response" tab and see if it contains a large JSON file with your songs (warning: There is a song track limit of 500, you may need to find another JSON file and combine them)
8. Save the JSON to a file and use that with this script