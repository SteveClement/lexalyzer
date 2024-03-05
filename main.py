#!/usr/bin/env python
import wave
import os
import sys
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
import isodate
from keys import api_key

youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_videos(channel_id):
    # Get the upload playlist ID
    res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    videos = []
    next_page_token = None

    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, part='snippet', maxResults=50, pageToken=next_page_token).execute()
        videos += res['items']
        next_page_token = res.get('nextPageToken')

        if next_page_token is None:
            break

    return videos

def print_video_durations(videos):
    for video in videos:
        video_id = video['snippet']['resourceId']['videoId']
        video_details = youtube.videos().list(id=video_id, part='contentDetails').execute()
        duration = video_details['items'][0]['contentDetails']['duration']
        duration_in_seconds = isodate.parse_duration(duration).total_seconds()
        print(f"Title: {video['snippet']['title']}, Duration: {duration_in_seconds} seconds, ID: {video_id}")


def download_audio(video_url, output_path='output/'):
    """Downloads audio from the given video URL using yt-dlp.

    Args:
    video_url (str): URL of the YouTube video.
    output_path (str): Directory to save the downloaded audio file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }

    with YoutubeDL(ydl_opts) as ydl:
        res = ydl.download([video_url]) # res seems to be the exit code of the download process
        

def symlink_audio(source, destination):
    try:
       os.symlink(source, destination)
       print(f"Symlink created successfully from {source} to {destination}")
    except OSError as e:
       print(f"Failed to create symlink: {e}")


# Analyze wav and return sample rate, bit rate, and format details
def analyze_wav(file_path):
    """
    Analyzes a WAV file and returns the frame rate, bit rate, and format details.

    Parameters:
    file_path (str): The path to the WAV file.

    Returns:
    tuple: A tuple containing the frame rate, bit rate, and format details.

    """
    # Open the WAV file
    with wave.open(file_path, 'rb') as wav_file:
        # Extract audio parameters
        n_channels = wav_file.getnchannels() # Number of channels
        sample_width = wav_file.getsampwidth() # Sample width in bytes
        frame_rate = wav_file.getframerate() # Sample rate
        n_frames = wav_file.getnframes() # Number of frames

        # Calculate duration in seconds
        duration = n_frames / frame_rate

        # Calculate bit rate
        bit_rate = frame_rate * sample_width * 8 * n_channels # in bits per second

        # Format details
        format_details = {
            'Number of Channels': n_channels,
            'Sample Width (bytes)': sample_width,
            'Frame Rate / Sample Rate (Hz)': frame_rate,
            'Number of Frames': n_frames,
            'Duration (seconds)': duration,
        }

        return frame_rate, bit_rate, format_details

channel_id = 'UCfnpkeDIEkPvbI1JljqvyAg'  # Replace 'CHANNEL_ID' with the actual channel ID
channel_id = 'UCygEo8mY_HUD8DZb-xboxRg'  # Replace 'CHANNEL_ID' with the actual channel ID

videos = get_channel_videos(channel_id)
print_video_durations(videos)

# Example usage:
#file_path = 'converted.wav'
#sample_rate, bit_rate, format_details = analyze_wav(file_path)
#print(f"Sample Rate: {sample_rate} Hz")
#print(f"Bit Rate: {bit_rate} bits/s")
#print("Format Details:")
#for key, value in format_details.items():
#    print(f"{key}: {value}")

if __name__ == '__main__':
    #if len(sys.argv) != 2:
    #    print("Usage: python script.py <YouTube Video URL>")
    #    sys.exit(1)

    # video_url = sys.argv[1]
    video_url = 'https://www.youtube.com/watch?v=eoXd76ONbVk'
    download_audio(video_url)
