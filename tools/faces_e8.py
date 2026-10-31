# 第8話の顔グラ（docs/ref/empire-08-faces.png）の切り抜き。名前の札はパネルの下なので、そのまま 128×128 に縮小して assets/faces に書く
from PIL import Image
im=Image.open('docs/ref/empire-08-faces.png').convert('RGB')
C={'mb_captain':(55,118,365,428),'elsa':(430,125,730,425),'hans':(815,120,1115,420),'comrade_mother':(1190,135,1480,425)}
sheet=Image.new('RGB',(138*len(C),148),'white')
for i,(n,b) in enumerate(C.items()):
    c=im.crop(b).resize((128,128),Image.LANCZOS);c.save(f'assets/faces/{n}.png');sheet.paste(c,(i*138,10))
sheet.save('/tmp/faces_e8_sheet.png')  # 確かめ用の一覧
