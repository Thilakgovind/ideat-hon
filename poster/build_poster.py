"""Print-ready Avvai A3/A4 idea poster using project and illustrative assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'poster'
OUT.mkdir(exist_ok=True)
W,H=3508,4961
INK='#19191d'; MUTED='#55565d'; PURPLE='#6559ef'; YELLOW='#ffdb3e'; PAPER='#f8f7f3'
REG=Path(r'C:\Windows\Fonts\segoeui.ttf'); BOLD=Path(r'C:\Windows\Fonts\segoeuib.ttf')
def f(n,b=False): return ImageFont.truetype(str(BOLD if b else REG),n)
def lines(d,string,width,font):
    result=[]
    for para in string.split('\n'):
        current=''
        for word in para.split():
            nextline=(current+' '+word).strip()
            if d.textlength(nextline,font=font)>width and current:
                result.append(current);current=word
            else:current=nextline
        result.append(current)
    return result
def drawtext(d,xy,string,size,color=INK,bold=False,width=None,leading=1.2):
    x,y=xy;ft=f(size,bold)
    for line in lines(d,string,width or W-x-180,ft):
        d.text((x,y),line,font=ft,fill=color)
        y+=int(size*leading)
    return y
def fit(src,size):
    w,h=size; scale=max(w/src.width,h/src.height);im=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.LANCZOS)
    x=(im.width-w)//2;y=(im.height-h)//2
    return im.crop((x,y,x+w,y+h))

im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
d.text((180,150),'AVVAI',font=f(110,True),fill=INK)
d.rounded_rectangle((2855,154,3325,256),radius=50,fill=YELLOW)
d.text((2930,178),'SDG 5',font=f(48,True),fill=INK)
d.line((180,310,3328,310),fill='#dfdedb',width=6)
drawtext(d,(180,385),'A fair chance needs\nmore than talent.',190,INK,True,2500,1.03)
drawtext(d,(185,815),'A Tamil-first companion for women athletes.',75,MUTED,False,2750)

trip=Image.open(Path(r'C:\Users\THILAK GOVIND\.codex\generated_images\01a197af-e2f8-7e80-ae96-35b8c7eb7d7a\exec-ce4c6306-1d34-475d-a6ab-a7b105bfac9c.png')).convert('RGB')
photo=fit(trip,(3148,1110));im.paste(photo,(180,1015));d=ImageDraw.Draw(im)
d.rounded_rectangle((208,1922,1730,2086),radius=35,fill='#14151de8')
drawtext(d,(255,1960),'ONE ATHLETE. THREE MOMENTS.',59,'#ffffff',True,1440)
drawtext(d,(180,2145),'Illustrative scenario · AI-generated visual, not survey footage',45,MUTED)

section_y=2290
for i,(phase,title,body) in enumerate([
    ('01  EMPATHY','The barriers','Travel cost and timing. Scattered trial notices. Private questions about periods, recovery and mental wellbeing.'),
    ('02  DEFINE','The question','How might women athletes find the right support, in their language, at the moment they need it?'),
    ('03  IDEATE','The answer','Ask Avvai by voice or text. Explore opportunities, travel, funding and wellbeing. Review each next step before acting.')]):
    x=180+i*1065
    d.rounded_rectangle((x,section_y,x+1005,section_y+770),radius=48,fill='#ffffff',outline='#e2e1dc',width=4)
    d.rounded_rectangle((x+53,section_y+58,x+545,section_y+150),radius=45,fill=YELLOW if i==2 else '#e9e7ff')
    drawtext(d,(x+90,section_y+83),phase,42,INK,True,460)
    drawtext(d,(x+53,section_y+208),title,75,INK,True,900)
    drawtext(d,(x+53,section_y+340),body,52,MUTED,False,900,1.28)

d.rounded_rectangle((180,3195,3328,4480),radius=55,fill='#171820')
drawtext(d,(290,3300),'THE WORKING PROTOTYPE',47,YELLOW,True,1640)
drawtext(d,(290,3410),'Speak. Discover.\nChoose your next step.',110,'#ffffff',True,1950,1.1)
drawtext(d,(290,3740),'Voice or text in Tamil, Tanglish or English. Relevant options for opportunities, travel, funding and wellbeing.',61,'#d9d9e2',False,1700,1.25)
drawtext(d,(290,4200),'Women stay in control of what they share and submit.',47,YELLOW,True,1870)
phone=Image.open(ROOT/'.codex/video-home.png').convert('RGB');phone=fit(phone,(785,1060))
im.paste(phone,(2380,3305));d=ImageDraw.Draw(im)
d.rounded_rectangle((2360,3285,3185,4385),radius=54,outline='#ffdb3e',width=19)

d.line((180,4580,3328,4580),fill='#d8d8d2',width=5)
drawtext(d,(180,4640),'NEXT: test the assumptions with real women athletes.',59,INK,True,3100)
drawtext(d,(180,4765),'Avvai · Ideathon idea submission · Design thinking: Empathy → Define → Ideate',42,MUTED,False,3140)

im.save(OUT/'Avvai_A3_colour_poster.png',dpi=(300,300))
im.save(OUT/'Avvai_A3_colour_poster.pdf',resolution=300.0)
a4=im.resize((2480,3508),Image.Resampling.LANCZOS)
a4.save(OUT/'Avvai_A4_colour_poster.pdf',resolution=300.0)
print(OUT/'Avvai_A3_colour_poster.pdf')
print(OUT/'Avvai_A4_colour_poster.pdf')
