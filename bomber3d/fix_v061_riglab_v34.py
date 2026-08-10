from pathlib import Path
import re

# Bomber3D: apply the Hunyuan global orientation discovered in Rig Lab.
p = Path('bomber3d/index.html')
s = p.read_text(encoding='utf-8')
s = s.replace("const GAME_VERSION='0.6.0',LAST_CHANGE='Traductor per-hueso: ejes + offset de pose aprendido con idle/run Hunyuan'", "const GAME_VERSION='0.6.1',LAST_CHANGE='Orientación global Hunyuan +90° X aplicada además del heading +90° Y'")
s = s.replace("const model=SkeletonUtils.clone(source);model.rotation.y=Math.PI/2;", "const model=SkeletonUtils.clone(source);model.rotation.x=Math.PI/2;model.rotation.y=Math.PI/2;")
p.write_text(s, encoding='utf-8')

# Rig Lab cleanup + immediate/independent model loading.
p = Path('bomber3d/rig-lab.html')
s = p.read_text(encoding='utf-8')

# Clean repeated UI/CSS blocks accumulated by old non-idempotent upgrade scripts.
css_block = ".dragHandle{cursor:grab;touch-action:none;user-select:none;padding:3px 5px;border-radius:6px;border:1px solid var(--line);color:var(--muted);font-weight:900}.moveGrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.moveBox{border:1px solid var(--line);border-radius:11px;padding:9px;background:#10151a}.moveRow{display:grid;grid-template-columns:22px 1fr 48px;gap:6px;align-items:center;margin:6px 0}"
while s.count(css_block) > 1:
    first = s.find(css_block)
    second = s.find(css_block, first + len(css_block))
    s = s[:second] + s[second + len(css_block):]

pill = '<span class="pill">reordená KayKit sólo desde ⋮⋮</span>'
while s.count(pill) > 1:
    pos = s.rfind(pill)
    s = s[:pos] + s[pos + len(pill):]

# Remove repeated model-position JS blocks, retaining the first one.
block_re = re.compile(r"\nfunction applyModelPos\(side\)\{.*?\$\('centerBoth'\)\.addEventListener\('click',\(\)=>\{resetModelPos\('h'\);resetModelPos\('k'\)\}\);\n", re.S)
blocks = list(block_re.finditer(s))
if len(blocks) > 1:
    for m in reversed(blocks[1:]):
        s = s[:m.start()] + '\n' + s[m.end():]

s = s.replace('RIG LAB v3.3', 'RIG LAB v3.4')
s = s.replace("version:'3.3'", "version:'3.4'")

# Replace loader so the scene renders immediately and each model is mounted as soon as its own asset arrives.
new_load = r'''async function load(){
initScene();animate();
$('load').textContent='cargando Hunyuan + KayKit…';
try{
 const hp=new Promise((res,rej)=>new FBXLoader().load('main_rigged.fbx?v=34',res,p=>{if(p.total)$('load').textContent='Hunyuan '+Math.round(p.loaded/p.total*100)+'% · KayKit cargando…'},rej));
 const kp=new Promise((res,rej)=>new GLTFLoader().load('../fightermp/Barbarian.glb?v=34',res,undefined,rej));
 let hReady=false,kReady=false;
 hp.then(h=>{hRoot=h;hSkin=findSkin(hRoot);if(!hSkin)throw Error('No encontré skeleton Hunyuan');hBones=hSkin.skeleton.bones;hSkin.skeleton.pose();hBones.forEach(b=>hRest.set(b.name,b.quaternion.clone()));hRoot.rotation.x=Math.PI/2;hRoot.rotation.y=0;fit(hRoot,2.15);hRoot.position.x-=1.35;hBasePos.copy(hRoot.position);scene.add(hRoot);hReady=true;$('load').textContent='✓ Hunyuan visible · KayKit cargando…'}).catch(e=>console.error(e));
 kp.then(k=>{kRoot=k.scene;kSkin=findSkin(kRoot);if(!kSkin)throw Error('No encontré skeleton KayKit');kBones=kSkin.skeleton.bones;kSkin.skeleton.pose();kBones.forEach(b=>kRest.set(b.name,b.quaternion.clone()));kRoot.rotation.set(0,0,0);fit(kRoot,2.15);kRoot.position.x+=1.35;kBasePos.copy(kRoot.position);scene.add(kRoot);kReady=true;$('load').textContent=hReady?'✓ ambos visibles':'✓ KayKit visible · Hunyuan cargando…'}).catch(e=>console.error(e));
 const [h,k]=await Promise.all([hp,kp]);
 if(!hSkin||!kSkin)throw Error('No encontré ambos skeletons');
 for(const [sel,bones] of [[$('hBone'),hBones],[$('kBone'),kBones]]){sel.innerHTML='';for(const b of bones){const o=document.createElement('option');o.value=b.name;o.textContent=`${role(b.name)||'—'} · ${b.name}`;sel.appendChild(o)}}
 buildMarkers();selectH(hBones.find(b=>role(b.name)==='hips')?.name||hBones[0].name);
 $('load').textContent=`✓ Hunyuan ${hBones.length} · KayKit ${kBones.length}`;$('load').className='pill ok';window.__rigLabReady={hBones:hBones.length,kBones:kBones.length,version:'3.4',hVisible:hReady,kVisible:kReady};
}catch(e){$('load').textContent='ERROR: '+e.message;$('load').className='pill warn';console.error(e)}}
'''
s, n = re.subn(r"async function load\(\)\{.*?\nfunction animate\(\)\{", new_load + "function animate(){", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('No pude reemplazar load() del Rig Lab')

p.write_text(s, encoding='utf-8')
