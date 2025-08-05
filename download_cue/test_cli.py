import unittest
import cli

class TestCue(unittest.TestCase):
    def test_format_cue_time(self):
        self.assertEqual(cli.format_cue_time(0), "00:00:00")
        self.assertEqual(cli.format_cue_time(3), "00:03:00")
        self.assertEqual(cli.format_cue_time(17), "00:17:00")
        self.assertEqual(cli.format_cue_time(65), "01:05:00")
        self.assertEqual(cli.format_cue_time(70*60+10), "70:10:00")

    def test_parse_time(self):
        self.assertEqual(cli.parse_time(""), 0)
        self.assertEqual(cli.parse_time("00:00"), 0)
        self.assertEqual(cli.parse_time("00:05"), 5)
        self.assertEqual(cli.parse_time("00:17"), 17)
        self.assertEqual(cli.parse_time("02:17"), 137)
        self.assertEqual(cli.parse_time("73:25"), 4405)
        self.assertEqual(cli.parse_time("2:03:25"), 7405)
        self.assertEqual(cli.parse_time("02:03:25"), 7405)
        self.assertEqual(cli.parse_time("12:03:25"), 43405)

    def test_remove_artist_prefix(self):
        self.assertEqual(cli.remove_artist_prefix(""), "")
        self.assertEqual(cli.remove_artist_prefix("Hello - World"), "World")
        self.assertEqual(cli.remove_artist_prefix("Hello World"), "Hello World")
        self.assertEqual(cli.remove_artist_prefix("Hello - There - World"), "There - World")

    def test_calculate_start_times(self):
        # Zero tracks. Should be invalid, though.
        self.assertEqual(cli.calculate_start_times([], 300), [])

        # Single tracks combinations.
        self.assertEqual(cli.calculate_start_times([0], 300), [0])
        self.assertEqual(cli.calculate_start_times([100], 300), [100])

        # All times are set, so nothing to do.
        self.assertEqual(cli.calculate_start_times([0, 100, 200], 300), [0, 100, 200])

        # No times are set, equally distributed.
        self.assertEqual(cli.calculate_start_times([0, 0, 0], 300), [0, 100, 200])

        # Just last set.
        self.assertEqual(cli.calculate_start_times([0, 0, 0, 0, 0, 550], 600), [0, 110, 220, 330, 440, 550])

        # Middle set.
        self.assertEqual(cli.calculate_start_times([0, 0, 0, 100, 0, 0], 600), [0, 33, 67, 100, 267, 433])

        # First is non-zero.
        self.assertEqual(cli.calculate_start_times([100, 0, 0, 0, 0, 0], 600), [100, 183, 267, 350, 433, 517])

    def test_fix_start_times(self):
        self.assertEqual(cli.fix_start_times({
            'tracks': [
                {'start_time': ''},
                {'start_time': ''},
                {'start_time': ''},
                {'start_time': '01:40'},
                {'start_time': ''},
                {'start_time': ''},
            ],
        }, 300), {
            'tracks': [
                {'start_time': '00:00:00'},
                {'start_time': '00:33:00'},
                {'start_time': '01:07:00'},
                {'start_time': '01:40:00'},
                {'start_time': '02:47:00'},
                {'start_time': '03:53:00'},
            ],
        })

    def test_build_cue(self):
        self.assertEqual(cli.build_cue({
            'album_artist': 'Album Artist',
            'album_title': 'Title Is Here',
            'tracks': [
                {'start_time': '', 'artist': 'Artist 1', 'title': 'Title 1'},
                {'start_time': '01:40', 'artist': 'Artist 2', 'title': 'Title 2'},
            ],
        }, 'file/path.mp3', 300), """
REM "This cue was build with https://github.com/elliotchance/download-cue"
PERFORMER "Album Artist"
TITLE "Title Is Here"
FILE "path.mp3" MP3
  TRACK 01 AUDIO
    PERFORMER "Artist 1"
    TITLE "Title 1"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    PERFORMER "Artist 2"
    TITLE "Title 2"
    INDEX 01 01:40:00
""".strip())
        
        self.assertEqual(cli.build_cue({
            'album_artist': '',
            'album_title': '',
            'tracks': [
                {'start_time': '', 'artist': '', 'title': ''},
                {'start_time': '01:40', 'artist': '', 'title': ''},
            ],
        }, 'file/path.mp3', 300), """
REM "This cue was build with https://github.com/elliotchance/download-cue"
FILE "path.mp3" MP3
  TRACK 01 AUDIO
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    INDEX 01 01:40:00
""".strip())

if __name__ == '__main__':
    unittest.main()
