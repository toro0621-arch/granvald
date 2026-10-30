# 第7話の顔グラ（docs/ref/empire-07-faces.png）の切り抜き。名前の札をパネルの背景色で塗ってから、128×128 に縮小して assets/faces に書く
from PIL import Image, ImageDraw
im=Image.open('docs/ref/empire-07-faces.png').convert('RGB');dr=ImageDraw.Draw(im)
# 名前の札（パネルの左上）：(左, 右, 背景色を取る点)
for L,R,bx in [(18,285,480),(522,755,985),(1030,1295,1495)]:
    dr.rectangle((L,100,R,168),fill=im.getpixel((bx,180)))
# 札にかかる髪を塗りつぶさないよう、札の下（y=170〜）から切る
C={'stahl':(125,170,395,440),'julius':(615,170,885,440),'berthold':(1120,170,1400,450)}
sheet=Image.new('RGB',(138*len(C),148),'white')
for i,(n,b) in enumerate(C.items()):
    c=im.crop(b).resize((128,128),Image.LANCZOS);c.save(f'assets/faces/{n}.png');sheet.paste(c,(i*138,10))
sheet.save('/tmp/faces_e7_sheet.png')  # 確かめ用の一覧
