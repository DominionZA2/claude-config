# Extract Video Steps Command

## Description
Downloads a screen recording video (Loom, or other supported URL) and extracts reproduction steps by analyzing video frames. Useful for converting tester bug report videos into actionable, written reproduction steps without needing to watch the video yourself.

## Usage
```
/extract-video-steps <video-url>
```

## Arguments
- `$ARGUMENTS` - The URL of the video to process (e.g. a Loom share link)

## Prerequisites
The following tools must be installed. If missing, install them via Homebrew:
- `yt-dlp` - for downloading videos from Loom and other platforms
- `ffmpeg` - for extracting frames from the downloaded video

```bash
brew install yt-dlp ffmpeg
```

## Behavior
When the `/extract-video-steps` command is executed, the system will:

1. **Validate Input**: Confirm a video URL was provided in `$ARGUMENTS`
2. **Check Tools**: Verify `yt-dlp` and `ffmpeg` are installed, install via `brew install` if missing
3. **Create Temp Directory**: Create a temporary working directory at `/tmp/video-extract-<timestamp>`
4. **Download Video**: Use `yt-dlp` to download the video file
5. **Extract Frames**: Use `ffmpeg` to extract one frame every 5 seconds as PNG images
6. **Analyze Frames**: Read every extracted frame image and visually analyze what is shown on screen
7. **Produce Reproduction Steps**: Write a structured bug report with numbered steps, observed problems, and expected behavior

## Implementation Steps

### 1. Validate Input
If `$ARGUMENTS` is empty or missing, ask the user for the video URL. Do not proceed without a URL.

### 2. Check and Install Tools
```bash
which yt-dlp || brew install yt-dlp
which ffmpeg || brew install ffmpeg
```

### 3. Create Working Directory
```bash
WORKDIR="/tmp/video-extract-$(date +%s)"
mkdir -p "$WORKDIR"
```

### 4. Download the Video
```bash
cd "$WORKDIR" && yt-dlp -o "video.%(ext)s" "<VIDEO_URL>"
```
If yt-dlp fails, report the error to the user. Some videos may be private or require authentication.

### 5. Extract Frames
```bash
ffmpeg -i "$WORKDIR/video.*" -vf "fps=1/5" "$WORKDIR/frame_%03d.png"
```
This extracts one frame every 5 seconds. For a 2-minute video this produces ~24 frames.

### 6. Analyze ALL Frames
Read every single extracted frame image using the Read tool. For each frame, note:
- What page/screen is shown
- What UI elements are visible (buttons, forms, dialogs, menus, lists)
- What the user appears to have clicked or interacted with
- Any loading spinners, error messages, or unexpected states
- Any developer tools or console output visible
- Any text content visible on screen (labels, field values, error messages)

**IMPORTANT**: Do not skip any frames. Every frame must be read and analyzed. The transitions between frames reveal the user's click path.

### 7. Produce the Output
Structure the output as follows:

```markdown
## Bug: <descriptive title based on what was observed>

**Application:** <app name from browser title/header>
**Reporter:** <if visible in the video metadata>
**Date:** <recording date>
**Duration:** <video length>

---

### Steps to Reproduce

**Flow 1: <name of first workflow tested>**

1. Step one...
2. Step two...
3. Step three...

**Flow 2: <name of second workflow if applicable>**

4. Continue numbering...

---

### Observed Problems

1. **Problem name** - Description of what went wrong
2. **Problem name** - Description of what went wrong

---
```

## Important Notes
- This command works with ANY video URL supported by yt-dlp (Loom, YouTube, Vimeo, direct MP4 links, etc.)
- Videos with no audio are expected - this command relies entirely on visual frame analysis
- If a video has audio/transcript, that's a bonus but not required - the frame analysis is the primary method
- For very long videos (>5 minutes), consider extracting frames every 10 seconds instead of 5 to keep frame count manageable
- Always clean up: mention the temp directory path so the user can delete it later if desired
- The quality of the output depends on reading EVERY frame - do not summarize or skip frames
