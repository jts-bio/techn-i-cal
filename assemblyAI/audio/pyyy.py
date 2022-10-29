import asyncio
from deepgram import Deepgram
import deepgram
DEEPGRAM_API_KEY = 'b4a9473c5aa41d28dab30dc5d60822f91c40cc78'
URL_TO_YOUR_FILE = 'https://github.com/jts-bio/techn-i-cal/blob/92bf97271c592dd460e9dfc8cfef921b0d386cfa/assemblyAI/audio/Why I Think Tylenol is Both Dangerous & Useless.mp3'
async def main():

    # Initialize the Deepgram SDK
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    FILE = 'URL_TO_YOUR_FILE'

    source = {
        'url': FILE
    }

    response = await asyncio.create_task(
        deepgram.transcription.prerecorded(
            source
        )
    )

    print(json.dumps(response, indent=4))

asyncio.run(main())