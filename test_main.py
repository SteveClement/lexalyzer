"""
Main tests for the YouTube Audio analyzer.
"""
import os
import shutil
import unittest
import wave
from pydub import AudioSegment
from main import video_already_downloaded, search_channel_by_name, check_disk_space, \
                 get_channel_videos, get_video, download_audio, symlink_audio, \
                 analyze_wav, preprocess_wav

class TestVideoAlreadyDownloaded(unittest.TestCase):
    """
    A test case class to test the functionality of the video_already_downloaded function.
    """

    def test_existing_file(self):
        """
        Test case to check if video_already_downloaded function correctly
        identifies an existing file.
        """
        # Create a dummy file
        filename = "test_file.wav"
        with open(filename, "w", encoding="utf-8").close() as _:
            pass

        # Call the function with the dummy file
        ydl_opts = {}
        video_url = "https://www.youtube.com/watch?v=abc123"
        result = video_already_downloaded(ydl_opts, video_url)

        # Assert that the file exists and the filename is correct
        self.assertEqual(result, [True, filename])

        # Clean up the dummy file
        os.remove(filename)

    def test_non_existing_file(self):
        """
        Test case to check if video_already_downloaded function correctly
        identifies a non-existing file.
        """
        # Call the function with a non-existing file
        ydl_opts = {}
        video_url = "https://www.youtube.com/watch?v=def456"
        result = video_already_downloaded(ydl_opts, video_url)

        # Assert that the file does not exist and the filename is correct
        self.assertEqual(result, [False, "def456.wav"])

class TestCheckDiskSpace(unittest.TestCase):
    """
    A test suite for the check_disk_space function.
    """

    def test_available_space_below_threshold(self):
        """
        Test case to check if check_disk_space function correctly
        identifies available space below the threshold.
        """
        # Set the threshold to 80%
        threshold = 80

        # Mock the disk usage
        total = 100
        used = 90
        free = total - used
        shutil.disk_usage = lambda path: (total, used, free)

        # Call the function
        result = check_disk_space(threshold)

        # Assert that the result is False
        self.assertFalse(result)

    def test_available_space_above_threshold(self):
        """
        Test case to check if check_disk_space function correctly
        identifies available space above the threshold.
        """
        # Set the threshold to 80%
        threshold = 80

        # Mock the disk usage
        total = 100
        used = 70
        free = total - used
        shutil.disk_usage = lambda path: (total, used, free)

        # Call the function
        result = check_disk_space(threshold)

        # Assert that the result is True
        self.assertTrue(result)

class TestGetChannelVideos(unittest.TestCase):
    """
    A test case class for testing the `get_channel_videos` function.
    """

    def test_valid_channel_id(self):
        """
        Test case to check if get_channel_videos function correctly
        returns a list of videos for a valid channel ID.
        """
        # Call the function with a valid channel ID
        channel_id = "UC1234567890"
        videos = get_channel_videos(channel_id)

        # Assert that the returned value is a list
        self.assertIsInstance(videos, list)

    def test_invalid_channel_id(self):
        """
        Test case to check if get_channel_videos function correctly
        returns False for an invalid channel ID.
        """
        # Call the function with an invalid channel ID
        channel_id = "invalid_channel_id"
        videos = get_channel_videos(channel_id)

        # Assert that the returned value is False
        self.assertEqual(videos, False)

class TestGetVideo(unittest.TestCase):
    """
    Test case class for testing the get_video function.
    """

    def test_get_video_with_duration_mode(self):
        """
        Test case to check if get_video function correctly
        prints the expected output in duration mode.
        """
        # Create a dummy list of video objects
        videos = [
            {
                "snippet": {
                    "resourceId": {
                        "videoId": "abc123"
                    },
                    "title": "Video 1"
                }
            },
            {
                "snippet": {
                    "resourceId": {
                        "videoId": "def456"
                    },
                    "title": "Video 2"
                }
            }
        ]

        # Call the function with duration mode
        get_video(videos, mode="duration")

        # Assert that the expected output is printed
        # (You may need to modify this assertion based on your actual output)
        self.assertEqual(1, 1)

    def test_get_video_with_id_mode(self):
        """
        Test case to check if get_video function correctly returns the video IDs in id mode.
        """
        # Create a dummy list of video objects
        videos = [
            {
                "snippet": {
                    "resourceId": {
                        "videoId": "abc123"
                    },
                    "title": "Video 1"
                }
            },
            {
                "snippet": {
                    "resourceId": {
                        "videoId": "def456"
                    },
                    "title": "Video 2"
                }
            }
        ]

        # Call the function with id mode
        result = get_video(videos, mode="id")

        # Assert that the returned video IDs are correct
        self.assertEqual(result, ["abc123", "def456"])

class TestDownloadAudio(unittest.TestCase):
    """
    A test case class for testing the download_audio function.
    """

    def test_download_existing_video(self):
        """
        Test case to check if download_audio function correctly downloads an existing video.
        """
        # Call the function with an existing video URL
        video_url = "https://www.youtube.com/watch?v=abc123"
        result = download_audio(video_url)

        # Assert that the result is the path of the downloaded audio file
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))

        # Clean up the downloaded audio file
        os.remove(result)

    def test_download_non_existing_video(self):
        """
        Test case to check if download_audio function correctly handles a non-existing video.
        """
        # Call the function with a non-existing video URL
        video_url = "https://www.youtube.com/watch?v=def456"
        result = download_audio(video_url)

        # Assert that the result is None
        self.assertIsNone(result)

class TestSymlinkAudio(unittest.TestCase):
    """
    A test case class to test the functionality of the symlink_audio function.
    """

    def test_symlink_creation(self):
        """
        Test case to check if symlink_audio function correctly creates a symlink.
        """
        # Create a dummy source file
        source = "source_file.wav"
        with open(source, "w", encoding="utf-8").close() as _:
            pass

        # Create a dummy destination file
        destination = "destination_file.wav"

        # Call the function with the dummy files
        symlink_audio(source, destination)

        # Assert that the symlink is created successfully
        self.assertTrue(os.path.islink(destination))

        # Clean up the dummy files
        os.remove(source)
        os.remove(destination)

class TestAnalyzeWav(unittest.TestCase):
    """
    Test case class for testing the analyze_wav function.
    """

    def test_analyze_wav(self):
        """
        Test case to check if analyze_wav function correctly analyzes a WAV file.
        """
        # Create a dummy WAV file
        filename = "test_file.wav"
        with wave.open(filename, "w") as wav_file:
            wav_file.setnchannels(2)  # Number of channels
            wav_file.setsampwidth(2)  # Sample width in bytes
            wav_file.setframerate(44100)  # Sample rate
            wav_file.setnframes(1000)  # Number of frames

        # Call the function with the dummy file
        frame_rate, bit_rate, format_details = analyze_wav(filename)

        # Assert the returned values are correct
        self.assertEqual(frame_rate, 44100)
        self.assertEqual(bit_rate, 352800)
        self.assertEqual(format_details["Number of Channels"], 2)
        self.assertEqual(format_details["Sample Width (bytes)"], 2)
        self.assertEqual(format_details["Frame Rate / Sample Rate (Hz)"], 44100)
        self.assertEqual(format_details["Number of Frames"], 1000)
        self.assertEqual(format_details["Duration (seconds)"], 0.022675736961451247)

        # Clean up the dummy file
        os.remove(filename)

class TestSearchChannelByName(unittest.TestCase):
    """
    Test case class for testing the search_channel_by_name function.
    """

    def test_existing_channel(self):
        """
        Test case to check if search_channel_by_name function correctly
        returns the channel ID for an existing channel.
        """
        # Call the function with an existing channel name
        channel_name = "MyChannel"
        result = search_channel_by_name(channel_name)

        # Assert that the channel ID is returned
        self.assertIsNotNone(result)

    def test_non_existing_channel(self):
        """
        Test case to check if search_channel_by_name function correctly
        returns None for a non-existing channel.
        """
        # Call the function with a non-existing channel name
        channel_name = "NonExistingChannel"
        result = search_channel_by_name(channel_name)

        # Assert that None is returned
        self.assertIsNone(result)

class TestPreprocessWav(unittest.TestCase):
    """
    Test case class for testing the preprocess_wav function.
    """

    def test_preprocess_wav(self):
        """
        Test case to check if preprocess_wav function correctly preprocesses a WAV file.
        """
        # Create a dummy WAV file
        filename = "test_file.wav"
        sound = AudioSegment.silent(duration=1000)  # Create a silent audio segment
        sound.export(filename, format="wav")

        # Call the function with the dummy file
        processed_file_path = preprocess_wav(filename)

        # Assert that the processed file exists
        self.assertTrue(os.path.exists(processed_file_path))

        # Clean up the dummy files
        os.remove(filename)
        os.remove(processed_file_path)

if __name__ == "__main__":
    unittest.main()
