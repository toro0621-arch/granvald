from PIL import Image, ImageDraw
# 第6話の顔グラ（docs/ref/empire-06-faces-a.png・-b.png）の切り抜き。名前の札をパネルの背景色で塗ってから、128×128 に縮小して assets/faces に書く
S='assets/faces/'
TAG={'a':[(18,175),(398,645),(780,990),(1160,1240)],'b':[(18,270),(398,660),(780,995),(1160,1340)]}
C={'a':{'emperor':(30,150,330,450),'marianne':(420,150,720,450),'lidia':(800,150,1100,450),'werner':(1185,166,1455,436)},
   'b':{'felix':(60,150,340,430),'guard':(430,150,710,430),'assassin':(805,150,1095,440),'zarg':(1170,150,1470,450)}}
sheet=Image.new('RGB',(138*8,148),'white');i=0
for f,d in C.items():
  im=Image.open(f'docs/ref/empire-06-faces-{f}.png').convert('RGB');dr=ImageDraw.Draw(im)
  for L,R in TAG[f]:
    col=im.getpixel(({18:360,398:738,780:1120,1160:1500}[L],175));dr.rectangle((L,100,R+6,169),fill=col)
  for n,b in d.items():
    c=im.crop(b).resize((128,128),Image.LANCZOS);c.save(S+n+'.png')
    sheet.paste(c,(i*138,10));i+=1
sheet.save('/tmp/faces_e6_sheet.png')  # 確かめ用の一覧
