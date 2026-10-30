from PIL import Image, ImageDraw
# 第6話の顔グラ（docs/ref/empire-06-faces-a.png・-b.png）の切り抜き。名前の札の下から切り、128×128 に縮小して assets/faces に書く
S='assets/faces/'
TAG={'a':[(18,175),(398,645),(780,990),(1160,1240)],'b':[(18,270),(398,660),(780,995),(1160,1340)]}
# 名前の札の下（y=170〜）から切る。札を塗りつぶすと、札にかかった髪や冠が平らに欠けて見えるため（ユーザーの指摘）。
# 頭の上は絵のふちでそろって切れるので、顔グラの枠に合わせて自然に見える
C={'a':{'emperor':(30,170,330,470),'marianne':(420,170,720,470),'lidia':(800,170,1100,470),'werner':(1185,170,1455,440)},
   'b':{'felix':(60,170,340,450),'guard':(430,170,710,450),'assassin':(805,170,1095,460),'zarg':(1170,170,1470,470)}}
sheet=Image.new('RGB',(138*8,148),'white');i=0
for f,d in C.items():
  im=Image.open(f'docs/ref/empire-06-faces-{f}.png').convert('RGB');dr=ImageDraw.Draw(im)
  for L,R in TAG[f]:
    col=im.getpixel(({18:360,398:738,780:1120,1160:1500}[L],175));dr.rectangle((L,100,R+6,169),fill=col)
  for n,b in d.items():
    c=im.crop(b).resize((128,128),Image.LANCZOS);c.save(S+n+'.png')
    sheet.paste(c,(i*138,10));i+=1
sheet.save('/tmp/faces_e6_sheet.png')  # 確かめ用の一覧
