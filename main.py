"""
Main code for the YouTube Audio analyzer.
"""
#!/usr/bin/env python
import wave
import os
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
import isodate
from pyAudioAnalysis import audioSegmentation as aS

try:
    from keys import api_key
    youtube = build('youtube', 'v3', developerKey=api_key)
except IOError as e:
    print(f"An error occurred: {e}")

def detect_speakers_and_durations(file_path):
    """
        Detects speakers in an audio file and calculates their durations.

        Returns:
            dict: A dictionary containing the durations of each speaker in a more readable format.
                The keys are in the format "Speaker <speaker_number>" and the values are the durations in seconds.
    """
    # Perform speaker diarization
    [flagsInd, classesAll, acc] = aS.speaker_diarization(file_path, 0, plot_res=False)

    # Initialize a dictionary to hold speaker durations
    speaker_durations = {}

    # Calculate the duration of each segment assuming a fixed window step in seconds (e.g., 0.2s as default in pyAudioAnalysis)
    window_step = 0.2

    for speaker_label in flagsInd:
        if speaker_label not in speaker_durations:
            speaker_durations[speaker_label] = window_step
        else:
            speaker_durations[speaker_label] += window_step

    # Convert speaker labels to a more readable format
    readable_speaker_durations = {f"Speaker {int(speaker) + 1}": duration for speaker, duration in speaker_durations.items()}

    return readable_speaker_durations

def video_already_downloaded(ydl_opts, video_url):
    """Check if the video has already been downloaded based on yt-dlp options."""
    with YoutubeDL(ydl_opts) as ydl:
        # Fetch video info without downloading
        info_dict = ydl.extract_info(video_url, download=False)
        filename = ydl.prepare_filename(info_dict)
        base = os.path.splitext(filename)[0] 
        filename = base + '.wav'
        print(f"Checking if {filename} exists: {os.path.exists(os.path.join(filename))}")
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
        res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
        if res['pageInfo']['totalResults'] == 0:
            print(f"Channel ID {channel_id} not found.")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
    
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

def get_video(videos, mode='id'):
    """
    Prints the duration of each video in the given list of videos.

    Args:
        videos (list): A list of video objects.

    Returns:
        None
    """
    if mode == 'duration':
        for video in videos:
            video_id = video['snippet']['resourceId']['videoId']
            video_details = youtube.videos().list(id=video_id, part='contentDetails').execute()
            duration = video_details['items'][0]['contentDetails']['duration']
            duration_in_seconds = isodate.parse_duration(duration).total_seconds()
            print(f"Title: {video['snippet']['title']}, Duration: {duration_in_seconds} seconds, ID: {video_id}")
    if mode == 'id':
        video_ids = []
        for video in videos:
            video_id = video['snippet']['resourceId']['videoId']
            video_ids.append(video_id)
            print(f"Title: {video['snippet']['title']}, ID: {video_id}")
        return video_ids


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
                'preferredquality': '192'
                }],
                'postprocessor_args': [
                '-ac', '1'  # This line ensures the audio is mono
                ],
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    alreadyDown, filename = video_already_downloaded(ydl_opts, video_url)
    if alreadyDown:
        print("Video has already been downloaded. Skipping download.")
        return filename

    with YoutubeDL(ydl_opts) as ydl:
        res = ydl.download([video_url]) # res seems to be the exit code of the download process


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

def search_channel_by_name(channel_name):
    search_response = youtube.search().list(
        q=channel_name,
        type='channel',
        part='id,snippet',
        maxResults=1
    ).execute()

    if search_response['items']:
        channel_id = search_response['items'][0]['id']['channelId']
        channel_title = search_response['items'][0]['snippet']['title']
        print(f"Channel ID: {channel_id}, Channel Title: {channel_title}")
        return channel_id
    else:
        print("Channel not found.")
        return None

##channel_id = 'UCfnpkeDIEkPvbI1JljqvyAg'  # Replace 'CHANNEL_ID' with the actual channel ID
##channel_id = 'UCygEo8mY_HUD8DZb-xboxRg'  # Replace 'CHANNEL_ID' with the actual channel ID

##videos = get_channel_videos(channel_id)
##if not videos:
##    print("No videos found.")
##else:
##    print_video_durations(videos)

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
    #video_url = 'https://www.youtube.com/watch?v=jrIJa2-niBM'
    #file_path = download_audio(video_url)
    #channel_name = 'Klonter77'  # This should be the name or a part of the custom URL

    channel_name = '@LexFridman'  # Replace 'CHANNEL_ID' with the actual channel ID
    channel_id = search_channel_by_name(channel_name)
    videos = get_video(get_channel_videos(search_channel_by_name(channel_name)), mode='id')

    for id in videos:
        download_audio(id, output_path='output/LexFridman/')    

    #file_path="output/test.wav"
    #speaker_durations = detect_speakers_and_durations(file_path)
    #for speaker, duration in speaker_durations.items():
    #    print(f"{speaker} talked for {duration:.2f} seconds")
