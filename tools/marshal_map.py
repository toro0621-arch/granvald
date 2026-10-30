# 元帥府の背景（docs/ref/bg-marshal.jpg）の壁の地図が、現実の世界地図に見えるので、
# このゲームの大陸の地図（assets/bg/continent.jpg）に貼り替えて assets/bg/marshal.jpg に書く
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
im=Image.open('docs/ref/bg-marshal.jpg').convert('RGB');a=np.asarray(im).astype(float)
X0,Y0,X1,Y1=0,230,165,740                      # 地図のあたり
reg=a[Y0:Y1,X0:X1];lum=reg.mean(2)
m=lum>105                                        # 羊皮紙（明るい）と壁（暗い木）を分ける
m=ndi.binary_closing(m,iterations=6);m=ndi.binary_fill_holes(m)
lab,n=ndi.label(m);m=lab==(np.bincount(lab.ravel())[1:].argmax()+1)  # いちばん大きいかたまり＝地図
# ふちの破れた縁は残す（画像の左端は地図が続いているので、端は削らない）
pad=np.pad(m,((0,0),(10,0)),mode='edge');inner=ndi.binary_erosion(pad,iterations=7)[:,10:];inner[:,:16]|=ndi.binary_erosion(m,iterations=7,border_value=1)[:,:16]
ys,xs=np.nonzero(inner);by0,by1,bx0,bx1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
cont=Image.open('assets/bg/continent.jpg').convert('RGB')
cw,ch=cont.size;bw,bh=bx1-bx0,by1-by0
# 大陸の地図の中ほど（帝国のあたり）を、地図の形に合わせて切り出す
cut_w=int(ch*0.62*bw/bh);cx=int(cw*0.5)
c=cont.crop((max(0,cx-cut_w//2),int(ch*0.12),min(cw,cx+cut_w//2),int(ch*0.74))).resize((bw,bh),Image.LANCZOS)
c=np.asarray(c.filter(__import__('PIL.ImageFilter',fromlist=['x']).GaussianBlur(.8))).astype(float)
c=c*.72+reg[by0:by1,bx0:bx1]*.28                 # 元の羊皮紙の色と陰影を少し残す
k=ndi.gaussian_filter(inner.astype(float),2)[by0:by1,bx0:bx1,None]
reg[by0:by1,bx0:bx1]=reg[by0:by1,bx0:bx1]*(1-k)+c*k
a[Y0:Y1,X0:X1]=reg
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('assets/bg/marshal.jpg',quality=85)
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).crop((0,200,300,760)).save('/tmp/marshal_chk.png')
