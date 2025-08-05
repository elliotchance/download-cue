#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup
import math
import sys
import os
from mutagen.mp3 import MP3

def download(url, file_name):
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/115.0.0.0 Safari/537.36'
      ),
      'Accept': (
          'text/html,application/xhtml+xml,application/xml;'
          'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
      ),
      'Accept-Language': 'en-US,en;q=0.9',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'DNT': '1',  # Do Not Track
  }

  response = requests.get(url, headers=headers)

  if response.ok:
      with open(file_name, "w", encoding='utf-8') as f:
          f.write(response.text)
  else:
      print(f"Failed to fetch: {response.status_code}")

def extract_tracklist_from_html(html_path):
  with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

  # Extract album title
  album_title_tag = soup.find('meta', {'itemprop': 'headline'})
  album_title = remove_artist_prefix(album_title_tag['content']) if album_title_tag else None

  # Extract album artist
  artist_tag = soup.find('a', href=lambda x: x and '/dj/' in x)
  album_artist = artist_tag.text.strip() if artist_tag else None

  # Extract each track
  tracks = []
  for item in soup.find_all('div', {'itemtype': 'http://schema.org/MusicRecording'}):
    try:
      artist = item.find('meta', {'itemprop': 'byArtist'})['content']
      title = remove_artist_prefix(item.find('meta', {'itemprop': 'name'})['content'])
      cue_input = item.find_previous('div', class_='bPlay').find('div', class_='cue')
      start_time = cue_input.text.strip() if cue_input else None

      tracks.append({
        'start_time': start_time,
        'artist': artist,
        'title': title
      })
    except Exception:
      continue  # Skip incomplete or malformed entries

  return {
    'album_title': album_title,
    'album_artist': album_artist,
    'tracks': tracks
  }

def get_audio_duration(filepath):
  if filepath.endswith('.mp3'):
    audio = MP3(filepath)
  else:
    raise Exception(f"Unsupported file: {filepath}")

  return audio.info.length

def remove_artist_prefix(s):
  parts = s.split(" - ")
  if len(parts) > 1:
    return ' - '.join(parts[1:])
  return s

def parse_time(s):
  if s == '':
    return 0

  parts = s.split(':')
  if len(parts) == 2:
    return int(parts[0]) * 60 + int(parts[1])
  if len(parts) == 3:
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

  raise Exception('cannot parse time: ' + s)

def format_cue_time(t):
  m = math.floor(t / 60)
  s = t % 60
  return f'{str(m).rjust(2, "0")}:{str(s).rjust(2, "0")}:00'

def calculate_start_times(start_times, total_time):
  new_start_times = start_times[:]
  total_tracks = len(new_start_times)
  if total_tracks == 0:
    return []

  # If no track times are set, we add a single anchor at the end.
  one_time_is_set = False
  for t in new_start_times:
    if t != 0:
      one_time_is_set = True
      break

  if not one_time_is_set:
    new_start_times[total_tracks-1] = round(total_time / total_tracks * (total_tracks - 1))

  while True:
    # Stop when there is no more zero track times (ignore the first one).
    is_done = True
    for t in new_start_times[1:]:
      if t == 0:
        is_done = False

    if is_done:
      break

    # Find start and end anchors.
    start_anchor = 0
    for t in new_start_times[1:]:
      start_anchor += 1
      if t == 0:
        break

    end_anchor = start_anchor
    for t in new_start_times[start_anchor:]:
      if t != 0:
        break
      end_anchor += 1

    start_time = new_start_times[start_anchor-1]
    if end_anchor >= len(new_start_times):
      end_time = total_time
    else:
      end_time = new_start_times[end_anchor]
    for i in range(end_anchor - start_anchor):
      new_start_times[i+start_anchor] = start_time + round((end_time - start_time) / (end_anchor - start_anchor + 1) * (i + 1))

  return new_start_times

def fix_start_times(tracklist, total_time):
  start_times = [parse_time(track['start_time']) for track in tracklist['tracks']]
  start_times = calculate_start_times(start_times, total_time)

  i = 0
  for track in tracklist['tracks']:
    track['start_time'] = format_cue_time(start_times[i])
    i += 1

  return tracklist

def build_cue(tracklist, file_path, total_time):
  tracklist = fix_start_times(tracklist, total_time)
  file_name = os.path.basename(file_path)
  cue_lines = [
    'REM "This cue was build with https://github.com/elliotchance/download-cue"'
  ]

  if tracklist["album_artist"]:
    cue_lines.append(f'PERFORMER "{tracklist["album_artist"]}"')

  if tracklist["album_title"]:
    cue_lines.append(f'TITLE "{tracklist["album_title"]}"')
  
  cue_lines.append(f'FILE "{file_name}" MP3')

  for i, track in enumerate(tracklist['tracks'], 1):
    cue_lines.append(f'  TRACK {i:02} AUDIO')

    if track['artist']:
      cue_lines.append(f'    PERFORMER "{track["artist"]}"')

    if track['title']:
      cue_lines.append(f'    TITLE "{track["title"]}"')

    cue_lines.append(f'    INDEX 01 {track["start_time"]}')

  return "\n".join(cue_lines)

def main():
  if len(sys.argv) < 3:
    print('usage: download-cue some/file.mp3 tracklist_url')
    exit(1)

  audio_file_path = sys.argv[1]
  url = sys.argv[2]
  cue_file_path = os.path.dirname(audio_file_path) + '/' + os.path.basename(audio_file_path)[:-4] + '.cue'
  file_name = "/tmp/tracklist.html"

  download(url, file_name)
  tracklist = extract_tracklist_from_html(file_name)

  with open(cue_file_path, 'w') as out:
    out.write(build_cue(tracklist, audio_file_path, get_audio_duration(audio_file_path)))
