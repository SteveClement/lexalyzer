#!/usr/bin/env python
"""
Main code for the YouTube Audio analyzer.
"""
# pylint:disable=no-member, line-too-long
import wave
import os
import shutil
import sys
import hashlib
import json
from pathlib import Path

import isodate
import librosa
import numpy as np

from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
from pyAudioAnalysis import audioSegmentation as aS
from pydub import AudioSegment

try:
    from keys import API_KEY
    youtube = build("youtube", "v3", developerKey=API_KEY)
except ModuleNotFoundError as error:
    print(f"An error occurred: {error} - Did you copy keys.py.sample to keys.py?")
    sys.exit(1)

DEBUG = True


def cleanup(path):
    """
    Recursively finds and deletes .part and .webm files in the specified directory.

    Args:
        path (str): The path to the directory to search for
        .part and .webm files.

    Returns:
        None
    """
    directory = Path(path)

    # Recursively find and delete .part and .webm files
    for filename in directory.rglob("*.part"):
        filename.unlink()
        print(f"Deleted: {filename}")
    for filename in directory.rglob("*.webm"):
        filename.unlink()
        print(f"Deleted: {filename}")


def seperator():
    """
    Prints a line of dashes that spans the width of the terminal window.
    """
    # Get the size of the terminal window
    columns = shutil.get_terminal_size()[0]

    # Fill the terminal with dashes until the end of the line
    for _ in range(1):
        print('-' * columns)


def hash_filename(filename):
    """
    Calculate the BLAKE2b hash digest of a given filename.

    Args:
        filename (str): The name of the file to hash.

    Returns:
        str: The hexadecimal representation of the hash digest.

    """
    # Create a BLAKE2b hash object
    hasher = hashlib.blake2b(digest_size=32)  # You can adjust `digest_size` as needed
    # Assuming the filename is a string, encode it to bytes
    hasher.update(filename.encode('utf-8'))
    # Return the hex digest of the hash
    return hasher.hexdigest()


def file_info_to_json(filename, hashed_filename, file_size, file_hash, format_details):
    """
    Converts file information to JSON format and writes it to a file.

    Args:
        filename (str): The original filename.
        hashed_filename (str): The hashed filename.
        file_size (int): The size of the file in bytes.
        file_hash (str): The hash value of the file.
        format_details (dict): A dictionary containing format details of the file.

    Returns:
        None
    """
    output_file = hashed_filename + '.json'
    # Data to be written to the JSON file
    data = {
        'original_filename': filename,
        'hashed_filename': hashed_filename,
        'file_size': file_size,
        'file_hash': file_hash,
        'channels': format_details['channels'],
        'sample_rate': format_details['sample_rate'],
        'duration': format_details['duration'],
        'file_name': format_details['file_name']
    }
    # Write the data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def preprocess_wav(file_path):
    """
    Preprocesses a WAV file by converting it to mono and setting the frame rate to 44.1 kHz.

    Args:
        file_path (str): The path to the input WAV file.

    Returns:
        str: The path to the processed WAV file.
    """
    sound = AudioSegment.from_wav(file_path)
    sound = sound.set_channels(1)  # Convert to mono
    sound = sound.set_frame_rate(44100)  # Convert to 44.1 kHz
    processed_file_path = "processed_" + file_path
    sound.export(processed_file_path, format="wav")
    return processed_file_path


def check_disk_space(threshold):
    """
    Checks the available disk space and returns False if it is below the specified threshold.

    Args:
        threshold (float): The minimum disk space threshold as a percentage.

    Returns:
        bool: False if the available disk space is below the threshold, True otherwise.
    """

    total, used, free = shutil.disk_usage("/")
    available_space_percentage = (free / total) * 100

    if DEBUG:
        print(f"Available space: {available_space_percentage:.2f}%")
        print(f"Used space: {used / (2**30):.2f} GB")

    if available_space_percentage < threshold:
        return False
    else:
        return True


def detect_speakers_and_durations(file_path):
    """
    Detects speakers in an audio file and calculates their durations.

    Returns:
        dict: A dictionary containing the durations of each speaker in a more readable format.
            The keys are in the format "Speaker <speaker_number>" and the values
            are the durations in seconds.
    """
    # Perform speaker diarization
    [flags_ind, classes_all, acc] = aS.speaker_diarization(file_path, 0, plot_res=False)

    if DEBUG:
        print(f"Speaker flags: {flags_ind}, Classes: {classes_all}", f"Accuracy: {acc}")
    # Initialize a dictionary to hold speaker durations
    speaker_durations = {}

    # Calculate the duration of each segment assuming a fixed window step in seconds
    # (e.g., 0.2s as default in pyAudioAnalysis)
    window_step = 0.2

    for speaker_label in flags_ind:
        if speaker_label not in speaker_durations:
            speaker_durations[speaker_label] = window_step
        else:
            speaker_durations[speaker_label] += window_step

    # Convert speaker labels to a more readable format
    readable_speaker_durations = {
        f"Speaker {int(speaker) + 1}": duration
        for speaker, duration in speaker_durations.items()
    }

    return readable_speaker_durations


def video_already_downloaded(ydl_opts, video_url):
    """Check if the video has already been downloaded based on yt-dlp options."""
    with YoutubeDL(ydl_opts) as ydl:
        # Fetch video info without downloading
        info_dict = ydl.extract_info(video_url, download=False)
        filename = ydl.prepare_filename(info_dict)
        base = os.path.splitext(filename)[0]
        filename = base + ".wav"
        if DEBUG:
            print(
                f"Checking if {filename} exists: {os.path.exists(os.path.join(filename))}"
            )
        # Check if the file exists in the output directory
        return [os.path.exists(os.path.join(filename)), filename]


def get_channel_videos(channel_id):
    """
    Retrieves a list of videos from a YouTube channel.

    Args:
        channel_id (str): The ID of the YouTube channel.

    Returns:
        list: A list of video objects from the channel's upload playlist.
    """
    # Get the upload playlist ID
    try:
        res = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        if res["pageInfo"]["totalResults"] == 0:
            print(f"Channel ID {channel_id} not found.")
            return False
    except ValueError as e:
        print(f"An error occurred: {e}")

    playlist_id = res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    next_page_token = None

    while True:
        res = (
            youtube.playlistItems()
            .list(
                playlistId=playlist_id,
                part="snippet",
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )
        videos += res["items"]
        next_page_token = res.get("nextPageToken")

        if next_page_token is None:
            break

    return videos


def get_video(videos, mode="id"):
    """
    Prints the duration of each video in the given list of videos.

    Args:
        videos (list): A list of video objects.

    Returns:
        None
    """
    if mode == "duration":
        for video in videos:
            video_id = video["snippet"]["resourceId"]["videoId"]
            video_details = (
                youtube.videos().list(id=video_id, part="contentDetails").execute()
            )
            duration = video_details["items"][0]["contentDetails"]["duration"]
            duration_in_seconds = isodate.parse_duration(duration).total_seconds()
            print(
                f"Title: {video['snippet']['title']}, \
                Duration: {duration_in_seconds} seconds, ID: {video_id}"
            )
        return None

    if mode == "id":
        video_ids = []
        for video in videos:
            video_id = video["snippet"]["resourceId"]["videoId"]
            video_ids.append(video_id)
            if DEBUG:
                print(f"Title: {video['snippet']['title']}, ID: {video_id}")
        return video_ids


def download_audio(video_url, output_path="output/", count=-1):
    """Downloads audio from the given video URL using yt-dlp.

    Args:
    video_url (str): URL of the YouTube video.
    output_path (str): Directory to save the downloaded audio file.
    count (int): Number of times to download the audio. -1 for infinite.

    Returns:
    str or None: The path of the downloaded audio file if successful, None otherwise.
    """

    if not check_disk_space(10):
        print("Disk space is below threshold. Aborting download.")
        sys.exit(31)

    # FIXME: Counter is not working as expected
    if count != -1:
        max_downloads = count
    else:
        max_downloads = 1

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,  # Suppresses most of the console output
        "no_warnings": True,  # Suppresses warning messages
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": ["-ac", "1"],  # This line ensures the audio is mono
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    already_down, filename = video_already_downloaded(ydl_opts, video_url)
    if already_down:
        if DEBUG:
            print("Video has already been downloaded. Skipping download.")
        return filename

    while count != 0:
        with YoutubeDL(ydl_opts) as ydl:
            try:
                res = ydl.download(
                    [video_url]
                )  # res seems to be the exit code of the download process
                if res != 0:
                    print(f"An error occurred while downloading video: {res}")
                    return None
                print(f"{count}/{max_downloads} downloads remaining.")
                count -= 1
                if count == 0:
                    break
            except IOError as e:
                print(f"An error occurred: {e}")
                return None

    return None


def symlink_audio(source, destination):
    """
    Create a symbolic link from the source file to the destination file.

    Args:
        source (str): The path of the source file.
        destination (str): The path of the destination file.

    Raises:
        OSError: If there is an error creating the symlink.

    Returns:
        None
    """
    try:
        os.symlink(source, destination)
        print(f"Symlink created successfully from {source} to {destination}")
    except OSError as ex:
        print(f"Failed to create symlink: {ex}")


def analyze_wav(file_path):
    """
    Analyzes a WAV file and returns its format details.

    Args:
        file_path (str): The path to the WAV file.

    Returns:
        dict: A dictionary containing the format details of the WAV file, 
              including the number of channels, sample rate, 
              duration in seconds, and file name.
    """
    # Open the WAV file
    with wave.open(file_path, "rb") as wav_file:
        # Extract audio parameters
        n_channels = wav_file.getnchannels()  # Number of channels
        frame_rate = wav_file.getframerate()  # Sample rate
        n_frames = wav_file.getnframes()  # Number of frames

        # Calculate duration in seconds
        duration = n_frames / frame_rate

        # Extract file name
        file_name = os.path.basename(file_path)

        # Format details
        format_details = {
            "channels": n_channels,
            "sample_rate": frame_rate,
            "duration": duration,
            "file_name": file_name
        }
        return format_details


def search_channel_by_name(channel_name):
    """
    Searches for a YouTube channel by name.

    Args:
        channel_name (str): The name of the channel to search for.

    Returns:
        str or None: The channel ID if found, None otherwise.
    """
    search_response = (
        youtube.search()
        .list(q=channel_name, type="channel", part="id,snippet", maxResults=1)
        .execute()
    )

    if search_response["items"]:
        channel_id = search_response["items"][0]["id"]["channelId"]
        channel_title = search_response["items"][0]["snippet"]["title"]
        if DEBUG:
            print(f"Channel ID: {channel_id}, Channel Title: {channel_title}")
        return channel_id
    else:
        print("Channel not found.")
        return None


def extract_features(file_path):
    """
    Extracts features from an audio file using MFCC.

    Parameters:
    file_path (str): The path to the audio file.

    Returns:
    numpy.ndarray: The mean MFCCs (Mel-frequency cepstral coefficients) of the audio file.
    """
    y, sr = librosa.load(file_path, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr)
    return np.mean(mfccs.T, axis=0)


def diarize(file_path):
    """
    Perform speaker diarization on an audio file.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        tuple: A tuple containing the speaker flags and classes.

    """
    [flags, classes, acc] = aS.speaker_diarization(file_path,
                                                   n_speakers=2,
                                                   mid_window=1,
                                                   mid_step=0.1,
                                                   short_window=0.05,
                                                   lda_dim=0)
    return flags, classes, acc


# #videos = get_channel_videos(channel_id)
# #if not videos:
# #    print("No videos found.")
# #else:
# #    print_video_durations(videos)

# Example usage:
# file_path = 'converted.wav'
# sample_rate, bit_rate, format_details = analyze_wav(file_path)
# print(f"Sample Rate: {sample_rate} Hz")
# print(f"Bit Rate: {bit_rate} bits/s")
# print("Format Details:")
# for key, value in format_details.items():
#    print(f"{key}: {value}")

if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #    print("Usage: python script.py <YouTube Video URL>")
    #    sys.exit(1)

    # video_url = sys.argv[1]
    # video_url = 'https://www.youtube.com/watch?v=jrIJa2-niBM'

    # TODO implement training for diacritization
    TRAINING = False
    CHANNEL_NAME = "@LexFridman"  # This should be the name or a part of the custom URL
    # TODO: Implement downloading only one video properly
    CHANNEL_VIDEO = "https://www.youtube.com/watch?v=0m3hGZvD-0s"
    CHANNEL_VIDEO = ["0m3hGZvD-0s", "1WpqQfmzBGY", "7Sk6lTLSZcA"]
    OUTPUT_PATH = "output/"

    if CHANNEL_VIDEO:
        COUNT = len(CHANNEL_VIDEO)
    else:
        COUNT = 3
    CHANNEL_ID = search_channel_by_name(CHANNEL_NAME)

    if not CHANNEL_VIDEO:
        VIDEOS = get_video(
            get_channel_videos(search_channel_by_name(CHANNEL_NAME)), mode="id"
        )
    else:
        VIDEOS = CHANNEL_VIDEO
    print(VIDEOS)

    for vid_id in VIDEOS:
        try:
            download_audio(vid_id, output_path=f"{OUTPUT_PATH}{CHANNEL_NAME}/", count=COUNT)
        except KeyboardInterrupt:
            print()
            seperator()
            print("Caught Ctrl-C (SIGINT), exiting gracefully...")
            cleanup(path=f"{OUTPUT_PATH}{CHANNEL_NAME}/")
            seperator()
            sys.exit(-1)

    # file_path="output/test.wav"
    # speaker_durations = detect_speakers_and_durations(file_path)
    # for speaker, duration in speaker_durations.items():
    #    print(f"{speaker} talked for {duration:.2f} seconds")
