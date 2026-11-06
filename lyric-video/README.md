# Lyric Studio

Open `lyric-video.html` from the tools site or any static HTTP server. No build, API keys, external fonts, libraries or uploads are required. All media stays in the browser's memory.

## Create a video

1. Load an MP3 (or another browser-decodable audio file) and a background image.
2. Paste lyrics, one phrase per line, and choose **Preparar letras**. Plain lyrics receive approximate equal-duration word timings, not automatic voice recognition. Standard LRC imports line timestamps and distributes words within each line; metadata, repeated timestamps and millisecond offsets are supported.
3. Choose **Sincronizar escuchando**. Tap the large button at each word onset, then once more at the end of the final word. Space also works when focus is outside a form control; the focused tap button supports its native keyboard activation. Slow playback to 0.75× or 0.5× for precise marking. Pause if needed. Cancelling preserves previous timings. The per-word editor allows gaps and precise start/end corrections, with validation against overlap and audio bounds.
4. Choose a palette, font, accent, lyric position, background darkness and motion. Long phrases paginate into at most three visual rows. Preview uses the same renderer and audio clock as export.
5. Export at 720×1280 or 1080×1920, 30 fps. Download the resulting file using the displayed link. MP4 is preferred when MediaRecorder supports it; otherwise the real format is WebM (never a renamed WebM). For workflows requiring MP4 specifically, use a browser with MP4 recording support or convert the WebM separately.

Export records in real time and includes the full audio track. Keep the tab visible: hiding it cancels recording rather than delivering frozen frames. Cancellation discards incomplete data. Settings and transport are locked during export. Export speed is always 1×, independent of rehearsal speed. Maximum audio duration is 20 minutes; available memory and browser encoding speed may impose lower practical limits, especially on phones. 720p is the recommended starting point. Browser support is detected at runtime.

**Guardar letras y estilo** exports a versioned JSON project with lyrics, word timings and style. Audio and image are intentionally not embedded: reload the originals when opening the project. Nothing is saved automatically; download the project before closing the page.

## Verification

Run `node --test lyric-video/timing.test.mjs` and `node --check lyric-video/app.mjs`. Browser smoke checks should cover audio/image loading, LRC import, manual synchronization, pause/seek, project round-trip, a short exported video with an audio track, cancellation, hidden-tab cancellation and narrow-screen layout.
