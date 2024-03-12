# TODO

[x] Download all videos from channel
[x] write fn: get_video_id * get_video_url
[x] get_channel_id_from_url: https://www.youtube.com/@lexfridman
[ ] Train dataset (check how to check if trained)

# Research notes

General approach you can take, utilizing Python libraries such as pydub for handling audio files, librosa for audio analysis, and pyAudioAnalysis or speaker-recognition for speaker diarization and recognition.

## Preprocess the Audio Files

Preprocessing might include converting files to a specific format, splitting them into smaller chunks, or normalizing the volume. [pydub](https://github.com/jiaaro/pydub) can be very helpful here but seems to be a little abandoned, [996cec4](https://github.com/jiaaro/pydub/commit/996cec42e9621701edb83354232b2c0ca0121560) 2 years ago. Possible useful fork: https://github.com/atsss/pydub
Converting files to mono and a sample rate of 44.1 kHz seems to be a good first step.

## Feature Extraction

Use librosa to extract features relevant for speaker recognition, such as MFCCs (Mel Frequency Cepstral Coefficients).

## Speaker Diarization

Speaker diarization can be complex, but libraries like pyAudioAnalysis simplify the process. The process involves segmenting the audio into speaker-homogeneous regions and then clustering these regions into groups corresponding to each speaker.

## Speaker Recognition

If you need to recognize who the speakers are (not just differentiate them), you might consider training a model with known voice samples using machine learning libraries like scikit-learn. The speaker-recognition library, although not updated recently, provides a good starting point for GMM-based speaker recognition.

## What are Mel Frequency Cepstral Coefficients?

Mel Frequency Cepstral Coefficients (MFCCs) are a type of feature widely used in speech and audio processing, especially in the fields of speech recognition and music information retrieval. They serve as a representation of the short-term power spectrum of sound, based on a linear cosine transform of a log power spectrum on a nonlinear mel scale of frequency.

Here's a breakdown of how MFCCs are computed and why they're useful:

* Pre-Emphasis: The first step often involves applying a pre-emphasis filter on the signal to amplify the high frequencies. This is done because human speech typically has higher energy at lower frequencies, and this step helps to balance the frequency spectrum.

* Framing: The audio signal is divided into short frames, typically 20-40 ms long. This is because the frequency content of audio signals changes over time, so analyzing these frames allows for the assumption of a stationary signal in each frame.

* Windowing: Each frame is then multiplied by a windowing function (such as a Hamming window) to minimize the signal discontinuities at the beginning and end of each frame.

* Fourier Transform: A Fast Fourier Transform (FFT) is applied to each windowed frame to obtain the spectrum.

* Mel Filter Bank Processing: The power spectrum is then passed through a series of filters called a mel filter bank. This step is crucial because the mel scale more closely approximates the human ear's response to sound, focusing on perceptually relevant frequencies. The mel scale emphasizes lower frequencies more than higher frequencies, which is similar to how humans perceive sound.

* Logarithmic Scaling: The logarithm of the energy output of each filter is then taken. This step mimics the human perception of loudness, which is also logarithmic.

* Discrete Cosine Transform (DCT): Finally, a discrete cosine transform (DCT) is applied to the log filter bank energies. The reason for using the DCT is to de-correlate the filter bank coefficients and yield a compact representation.

* The resulting coefficients (MFCCs) provide a representation of the audio signal's power spectrum that is compact and relevant to human auditory perception. Typically, the first 12-13 coefficients are used for basic applications, with the first coefficient sometimes being omitted because it represents the mean signal energy, which may not be informative for all applications.

* MFCCs are effective for various tasks because they capture key spectral properties in a way that aligns with human auditory perception, making them highly useful for speech recognition, speaker identification, music genre classification, and more.

## What are speaker diarization techniques?

Speaker diarization is the process of partitioning an audio stream into homogeneous segments according to the identity of the speaker. It's like figuring out "who spoke when" in a recording that involves multiple speakers. This process is crucial for various applications, such as meeting transcription, enhancing automatic speech recognition systems, and indexing audio archives. Speaker diarization techniques generally involve several key steps:

* Speech Detection: The first step is to distinguish between speech and non-speech segments within the audio stream. This process, also known as voice activity detection (VAD), filters out parts of the audio that do not contain speech, such as music, silence, or background noise.

* Speaker Segmentation: This involves breaking down the speech segments further into smaller parts, which are hypothesized to contain speech from individual speakers. The goal here is to create segments that are pure, meaning each segment should ideally contain speech from only one speaker.

* Feature Extraction: For each segment, relevant features are extracted that help in distinguishing between speakers. These features can include spectral information, prosody, and voice characteristics such as pitch and tone.

* Speaker Clustering: In this step, the extracted features are used to group segments together based on their similarity. The aim is to cluster segments that are believed to be spoken by the same person. Techniques used for clustering include Gaussian Mixture Models (GMM), Hidden Markov Models (HMM), and more recently, deep learning approaches such as deep neural networks (DNNs) and convolutional neural networks (CNNs).

* Speaker Labeling: After clustering, each cluster is labeled with a unique speaker identity. This step may involve mapping the speaker clusters to known speaker identities (in speaker recognition tasks) or simply assigning arbitrary labels in tasks where the actual identity of the speakers is not known or not important.

* Re-segmentation and Refinement: Often, an additional step is included to refine the initial segmentation and clustering. This may involve using more sophisticated models to re-evaluate and adjust the boundaries between segments or to merge or split clusters based on additional information. This step can significantly improve the accuracy of the diarization outcome.

* Recent advancements in speaker diarization have leveraged deep learning to improve each of these steps, particularly in feature extraction and speaker clustering, leading to more accurate diarization outcomes. Deep learning models can automatically learn complex patterns in speech that differentiate speakers, making them more effective in challenging diarization scenarios with overlapping speech, varying audio quality, or a large number of speakers.

## Important Considerations

The effectiveness of speaker diarization and recognition heavily depends on the quality of your audio files and the distinctiveness of the speakers' voices.
Some of the libraries mentioned, like pyAudioAnalysis and speaker-recognition, have their complexities and might require you to delve into their documentation and perhaps tweak parameters to get optimal results.
For more advanced and accurate speaker recognition, consider deep learning approaches, which might require significantly more data and computational resources.
This workflow should give you a starting point for analyzing a batch of WAV files to determine the speakers. Remember, each step might need adjustments based on your specific requirements and the characteristics of your audio files.