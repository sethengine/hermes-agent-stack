---
name: media-content-tools
description: "Find, analyze, and transform media content: YouTube transcripts, GIF search, and audio visualization."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Media, YouTube, GIF, Audio, Transcript, Visualization, Search]
---

# Media Content Tools

Extract, search, and visualize media content from popular platforms.

---

## YouTube Transcripts

Extract transcripts from YouTube videos and convert them into structured formats.

### Setup
```bash
pip install youtube-transcript-api
```

### Fetch transcript
```bash
# JSON with metadata
python3 scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text
python3 scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback
python3 scripts/fetch_transcript.py "URL" --lang en --fallback en,es,ja
```

### Transform
Use the transcript to generate:
- Chapter summaries
- Blog posts
- Twitter/X threads
- Study notes

---

## GIF Search (Tenor)

Search and download GIFs via the Tenor API.

### Setup
Set `TENOR_API_KEY` in `~/.hermes/.env` (get free key at https://developers.google.com/tenor/guides/quickstart).

### Search
```bash
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'
```

---

## Audio Visualization (songsee)

Generate spectrograms and audio feature visualizations.

### Setup
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

### Usage
```bash
# Basic spectrogram
songsee track.mp3

# Multi-panel grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg
```

### Visualization types
`spectrogram`, `mel`, `chroma`, `hpss`, `selfsim`, `loudness`, `tempogram`, `mfcc`, `flux`
