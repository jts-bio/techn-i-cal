# %%
# importing packages
from pytube import YouTube
import os
import asyncio, json

# url input from user
yt = YouTube(
	str(input("Enter the URL of the video you want to download: \n>> ")))

# extract only audio
video = yt.streams.filter(only_audio=True).first()

# check for destination to save file
print("Enter the destination (leave blank for current directory)")
destination = str(input(">> ")) or '.'

# download the file
out_file = video.download(output_path=destination)

# save the file
base, ext = os.path.splitext(out_file)
new_file = base + '.mp3'
os.rename(out_file, new_file)

# result of success
print(yt.title + " has been successfully downloaded.")


# %%
PATH_TO_FILE = '/workspace/techn-i-cal/Why I Think Tylenol is Both Dangerous & Useless.mp3'
MIMETYPE_OF_FILE = 'mp3'

# %%
from deepgram import Deepgram
DEEPGRAM_API_KEY = 'b4a9473c5aa41d28dab30dc5d60822f91c40cc78'
dg_client        = Deepgram(DEEPGRAM_API_KEY)

# %%
with open(PATH_TO_FILE, 'rb') as audio:
  source = {'buffer': audio, 'mimetype': MIMETYPE_OF_FILE}

print(source)

# %%
async def main():
    # Initializes the Deepgram SDK
    dg_client = Deepgram(DEEPGRAM_API_KEY)
    source = source
    options = { "punctuate": True, "model": "general", "language": "en", "tier": "enhanced" }

    print('Requesting transcript...')
    print('Your file may take up to a couple minutes to process.')
    print('While you wait, did you know that Deepgram accepts over 40 audio file formats? Even MP4s.')
    print('To learn more about customizing your transcripts check out developers.deepgram.com')

    response = await dg_client.transcription.prerecorded(source, options)
    print(json.dumps(response, indent=4))

asyncio.run(main())