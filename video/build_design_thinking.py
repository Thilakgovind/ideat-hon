"""Build the Avvai ideathon design-thinking film from local, labelled assets."""
from pathlib import Path
import math
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "video" / "output"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 720
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
TAMIL = Path(r"C:\Windows\Fonts\Nirmala.ttf")
ILLUSTRATION = Path(r"C:\Users\THILAK GOVIND\.codex\generated_images\01a197af-e2f8-7e80-ae96-35b8c7eb7d7a\exec-ce4c6306-1d34-475d-a6ab-a7b105bfac9c.png")
TRIPTYCH = Image.open(ILLUSTRATION).convert("RGB")
PANELS = [TRIPTYCH.crop((i * TRIPTYCH.width // 3, 0, (i + 1) * TRIPTYCH.width // 3, TRIPTYCH.height)) for i in range(3)]

def font(n, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), n)

def fit(im, box):
    x, y, w, h = box
    scale = max(w / im.width, h / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    return im.crop(((nw-w)//2, (nh-h)//2, (nw+w)//2, (nh+h)//2))

def text(d, xy, words, size, color, bold=False, max_width=None, gap=1.17):
    f = font(size, bold)
    x, y = xy
    lines = []
    for paragraph in words.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if max_width and d.textlength(candidate, font=f) > max_width and line:
                lines.append(line); line = word
            else:
                line = candidate
        lines.append(line)
    for line in lines:
        d.text((x,y), line, font=f, fill=color)
        y += round(size * gap)
    return y

def base(dark=False):
    im = Image.new("RGB", (W,H), "#15161d" if dark else "#f7f6f2")
    d = ImageDraw.Draw(im)
    d.text((66,45), "AVVAI  /  DESIGN THINKING", font=font(20, True), fill="#ffdc43" if dark else "#5a51d8")
    d.text((1090,45), "SDG 5", font=font(20, True), fill="#ffdc43" if dark else "#5a51d8")
    d.line((66,83,1214,83), fill="#ffffff33" if dark else "#dcdcd8", width=2)
    return im, d

def pill(d, label, x=66, y=122, fill="#ffda3b", fg="#18191d"):
    f=font(20,True); width=round(d.textlength(label,font=f))+38
    d.rounded_rectangle((x,y,x+width,y+39),radius=20,fill=fill)
    d.text((x+19,y+7),label,font=f,fill=fg)

def image_card(im, source, box):
    x,y,w,h=box
    shadow=Image.new("RGBA",(w+36,h+36),(0,0,0,0)); sd=ImageDraw.Draw(shadow)
    sd.rounded_rectangle((16,16,w+20,h+20),radius=27,fill=(0,0,0,60))
    shadow=shadow.filter(ImageFilter.GaussianBlur(14))
    im.paste(shadow,(x-18,y-12),shadow)
    cropped=fit(source,(0,0,w,h)); mask=Image.new('L',(w,h),0); md=ImageDraw.Draw(mask)
    md.rounded_rectangle((0,0,w,h),radius=22,fill=255)
    im.paste(cropped,(x,y),mask)

def phone(im, path, x=860, y=101, height=560):
    src=Image.open(path).convert('RGB')
    width=round(height*src.width/src.height)
    sh=Image.new('RGBA',(width+44,height+44),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.rounded_rectangle((17,17,width+27,height+27),radius=44,fill=(0,0,0,75))
    sh=sh.filter(ImageFilter.GaussianBlur(15)); im.paste(sh,(x-20,y-10),sh)
    d=ImageDraw.Draw(im);d.rounded_rectangle((x-9,y-9,x+width+9,y+height+9),radius=35,fill='#16171c')
    src=src.resize((width,height),Image.Resampling.LANCZOS)
    mask=Image.new('L',(width,height),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((0,0,width,height),radius=27,fill=255)
    im.paste(src,(x,y),mask)

scenes=[]
im,d=base(True); pill(d,"THE CHALLENGE",fill="#ffda3b")
text(d,(66,222),"A fair chance\nneeds more than talent.",62,"#ffffff",True,690)
text(d,(66,438),"One athlete. Many small barriers.\nOne connected way forward.",29,"#d3d2d8",max_width=700)
image_card(im,PANELS[0],(850,120,350,530));scenes.append((im,7))

for idx,(panel,stage,headline,body) in enumerate([
    (0,"EMPATHY / TRAVEL","The trial is across town.","The route, cost and timing all matter before she can even begin."),
    (1,"EMPATHY / OPPORTUNITY","The notice is easy to miss.","A scattered message can mean a missed trial, scholarship or sponsor."),
    (2,"EMPATHY / WELLBEING","Training has a hidden cost.","Periods, recovery and mental strain deserve private, practical support.")]):
    im,d=base();image_card(im,PANELS[panel],(66,118,510,525));pill(d,stage,x=636,y=145)
    text(d,(636,221),headline,52,"#18191d",True,550)
    text(d,(636,388),body,27,"#5f6068",max_width=540)
    text(d,(636,590),"ILLUSTRATIVE SCENARIO · NOT SURVEY FOOTAGE",17,"#827e7d",True)
    scenes.append((im,10))

im,d=base(True);pill(d,"DEFINE",fill="#ffda3b")
text(d,(66,202),"How might we make\nsupport easier to reach?",58,"#ffffff",True,1100)
text(d,(66,417),"One place to ask. Clear options to compare.\nHer choice before any request is sent.",31,"#d6d4dd",max_width=1050)
d.rounded_rectangle((66,583,1214,645),radius=17,fill="#292735")
text(d,(91,599),"TOOLS: PERSONA  →  JOURNEY MAP  →  HOW MIGHT WE",22,"#ffdc43",True)
scenes.append((im,8))

im,d=base();pill(d,"IDEATE",fill="#ffda3b")
text(d,(66,207),"Meet Avvai.",68,"#18191d",True)
text(d,(66,307),"A Tamil-first companion for women athletes:",30,"#5b5b63",max_width=700)
for i,(num,label) in enumerate([("01","Find a relevant opportunity"),("02","Plan travel and funding"),("03","Ask about mind and body")]):
    y=395+i*82;d.rounded_rectangle((66,y,735,y+64),radius=14,fill="#ffffff",outline="#e6e5e0",width=2)
    text(d,(88,y+14),num,24,"#6257db",True);text(d,(153,y+15),label,23,"#26272a",True)
phone(im,ROOT/'.codex/video-home.png',x=893,y=101,height=550)
scenes.append((im,9))

for label,headline,body,path,duration in [
    ("PROTOTYPE / VOICE","Speak in your language.","Avvai hears Tamil, Tanglish or English and offers a next step.",ROOT/'.codex/video-voice.png',10),
    ("PROTOTYPE / DISCOVER","See what fits you.","Explore opportunities, travel, funding and wellbeing in one flow.",ROOT/'.codex/video-opportunities.png',10),
]:
    im,d=base();pill(d,label);text(d,(66,223),headline,55,"#1b1b20",True,650)
    text(d,(66,381),body,28,"#5f6066",max_width=655)
    d.rounded_rectangle((66,550,745,626),radius=16,fill="#ffda3b")
    text(d,(90,571),"PROTOTYPE DEMO · CURRENT APP SCREEN",20,"#1a1a1d",True)
    phone(im,path,x=852,y=106,height=553);scenes.append((im,duration))

im,d=base(True);pill(d,"OUR TESTABLE IDEA",fill="#ffda3b")
text(d,(66,201),"Less searching.\nMore showing up.",70,"#ffffff",True,1000)
text(d,(66,440),"Avvai connects a question to an actionable option.\nWomen remain in control of every next step.",28,"#d9d7dd",max_width=1060)
text(d,(66,622),"Next: test these assumptions with real athletes.",21,"#ffdc43",True)
scenes.append((im,7))

for i,(im,duration) in enumerate(scenes):
    im.save(OUT/f"scene_{i:02}.png")

with (OUT/'scenes.txt').open('w',encoding='utf-8') as f:
    for i,(_,duration) in enumerate(scenes):
        f.write(f"file '{(OUT/f'scene_{i:02}.png').as_posix()}'\nduration {duration}\n")
    f.write(f"file '{(OUT/f'scene_{len(scenes)-1:02}.png').as_posix()}'\n")

ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg,'-y','-f','concat','-safe','0','-i',str(OUT/'scenes.txt'),'-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','22','-t','81',str(OUT/'visuals.mp4')],check=True)
print('Rendered visuals:',OUT/'visuals.mp4')
