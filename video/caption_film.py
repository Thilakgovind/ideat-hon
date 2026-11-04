"""Burn readable captions into the 81-second first-person Avvai film."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
CAP=OUT/'caption_frames'
CAP.mkdir(parents=True,exist_ok=True)
FONT=ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf',28)
BOLD=ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf',16)

# Caption timings are matched to the offline voiceover; the separate SRT is editable.
cues=[
 (0,5,'I am Meena, a fictional athlete representing questions we want to test.'),
 (5,9,'I love running. But getting to a trial is not just about training.'),
 (9,14,'I need to know the route, the cost, and whether I can get home safely.'),
 (14,18,'Sometimes the opportunity itself reaches me too late,'),
 (18,22,'buried in messages and different websites.'),
 (22,27,'I want a place where I can ask about my period, recovery,'),
 (27,31,'or how I am feeling, without being judged.'),
 (31,36,'I do not want someone deciding for me. I want clear choices.'),
 (36,41,'Could one companion help me find the right support when I need it?'),
 (41,46,'With Avvai, I can speak in Tamil, Tanglish, or English.'),
 (46,51,'I can look for an opportunity, plan my travel, explore funding,'),
 (51,56,'and open a private wellbeing conversation.'),
 (56,60,'Avvai shows me an option. I decide what to do.'),
 (60,65,'This is our working prototype.'),
 (65,70,'Now we need to listen to real athletes and test these assumptions,'),
 (70,75,'then improve Avvai with them.'),
]

def stamp(s):
    return f'00:{s//60:02}:{s%60:02},000'
with (OUT/'avvai_captions.srt').open('w',encoding='utf-8') as f:
    for i,(a,b,line) in enumerate(cues,1):
        f.write(f'{i}\n{stamp(a)} --> {stamp(b)}\n{line}\n\n')

def split_line(d,words,max_width):
    rows=[]; row=''
    for word in words.split():
        proposed=(row+' '+word).strip()
        if d.textlength(proposed,font=FONT)>max_width and row:
            rows.append(row);row=word
        else:row=proposed
    rows.append(row)
    return rows

for second in range(81):
    image=Image.new('RGBA',(1280,720),(0,0,0,0)); d=ImageDraw.Draw(image)
    line=next((line for a,b,line in cues if a<=second<b),'')
    if line:
        rows=split_line(d,line,1110)
        top=720-(39*len(rows)+55)
        d.rounded_rectangle((52,top-18,1228,710),radius=18,fill=(10,11,16,220))
        d.text((78,top-4),'MEENA · ILLUSTRATIVE PERSONA',font=BOLD,fill='#ffdf4b')
        for j,row in enumerate(rows):
            width=d.textlength(row,font=FONT)
            d.text(((1280-width)/2,top+20+j*37),row,font=FONT,fill='white')
    image.save(CAP/f'caption_{second:03}.png')

ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-y','-i',str(OUT/'visuals.mp4'),'-framerate','1','-i',str(CAP/'caption_%03d.png'),'-i',str(OUT/'athlete_voiceover.wav'),'-i',str(OUT/'score.wav'),
    '-filter_complex','[0:v][1:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[v];[2:a]volume=1.5,apad=pad_dur=81[n];[3:a]volume=0.45[m];[n][m]amix=inputs=2:duration=longest:dropout_transition=0[a]',
    '-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','192k','-t','81','-movflags','+faststart',str(OUT/'avvai_design_thinking_first_person_81s.mp4')],check=True)
print(OUT/'avvai_design_thinking_first_person_81s.mp4')
