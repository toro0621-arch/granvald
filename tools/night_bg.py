# 昼の会話の背景画を夜にする（明るさを落として青に寄せ、空を暗くする）。
# 使い方：python3 tools/night_bg.py <元の絵> <出力>  例：python3 tools/night_bg.py docs/ref/bg-pass.jpg assets/bg/pass_night.jpg
import sys
import numpy as np
from PIL import Image
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)/255
lum=im.mean(axis=2,keepdims=True)
night=lum*np.array([0.42,0.52,0.85])*0.75+im*0.08
h=im.shape[0];sky=np.clip(1-np.arange(h)/(h*0.45),0,1)[:,None,None]
night=night*(1-0.35*sky)+np.array([0.05,0.07,0.16])*sky*0.6
Image.fromarray((np.clip(night,0,1)*255).astype('uint8')).save(sys.argv[2],quality=85)
