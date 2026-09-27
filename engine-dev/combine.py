import sys
from PIL import Image
fs=sys.argv[2:]; ims=[Image.open(f) for f in fs]
W=max(i.width for i in ims); H=sum(i.height for i in ims)
out=Image.new('RGB',(W,H),'white'); y=0
for i in ims: out.paste(i,(0,y)); y+=i.height
if out.width>1600: out=out.resize((1600,int(out.height*1600/out.width)))
out.save(sys.argv[1],quality=78)
