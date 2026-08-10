from pathlib import Path
p=Path('bomber3d/rig-lab.html')
s=p.read_text(encoding='utf-8')
old=s
s=s.replace('RIG LAB v3.2','RIG LAB v3.3')
s=s.replace("hRoot.rotation.x=-Math.PI/2;hRoot.rotation.y=0;", "hRoot.rotation.x=Math.PI/2;hRoot.rotation.y=0;")
s=s.replace("version:'3.2'", "version:'3.3'")
if s!=old:
    p.write_text(s,encoding='utf-8')
    print('Rig Lab upgraded to v3.3')
else:
    print('Rig Lab v3.3 already applied or expected pattern not found')
