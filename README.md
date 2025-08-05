# download-cue

Download cue files for your mp3 files.

This currently only supports 1001tracklists.com, but I'm happy to add more - just create an issue!

# Installing/Updating

```sh
pip install download-cue
```

# Usage

```sh
# download-cue <file> <url>

download-cue "my/file.mp3" "https://www.1001tracklists.com/tracklist/1pc52051/noisia-vision-radio-s01e01-2021-01-06.html"
```

You will not see any output on success. The `.cue` fill will be created in the
same directory as `file.mp3` and will use the same name: `file.cue`.

**Note:** Remember to put quotes around paths and URLs.

# Notes

1. Not all tracks on 1001tracklists have start times. If missing, the start
   times will be estimated by dividing the tracks around any known start times.
