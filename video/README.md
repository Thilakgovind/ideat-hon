# Avvai design thinking film

Final video: [`output/avvai_design_thinking_first_person_81s.mp4`](output/avvai_design_thinking_first_person_81s.mp4) (81 seconds, 16:9, first-person female narration, burned-in captions).

## Story

1. Empathy: an illustrative Tamil Nadu athlete faces travel, opportunity discovery, and wellbeing barriers.
2. Define: how might we make relevant support easier to find and act on?
3. Ideate: a Tamil-first companion that connects a question to travel, funding, opportunities, and wellbeing support.
4. Prototype: current Avvai home, voice, and opportunity screens.
5. Next step: validate assumptions with real athletes.

The athlete image is AI-generated and is labelled **illustrative scenario, not survey footage**. The character "Meena" is fictional. The video makes no claim that interviews or a survey have already happened. The app screenshots are captured from the local prototype. The narration uses the operating system's offline female English voice. The portrait is a still image, not a lip-synced performance.

Rebuild the still visuals with `python video/build_design_thinking.py` after capturing current screenshots in `.codex/video-{home,voice,opportunities}.png`. The script requires Pillow and `imageio-ffmpeg`. The final audio mix also uses `video/output/narration.wav` and `video/output/score.wav`.

To regenerate the captioned version after recording `video/output/athlete_voiceover.wav`, run `python video/caption_film.py`. Edit `video/athlete_voiceover.txt` and the caption timings in `caption_film.py` together. An editable SRT is saved at `video/output/avvai_captions.srt`.
