from pathlib import Path

p = Path('bomber3d/index.html')
s = p.read_text(encoding='utf-8')
old = s

if "const GAME_VERSION='0.5.5'" not in s:
    print('No upgrade needed')
    raise SystemExit(0)

s = s.replace("const GAME_VERSION='0.5.5'", "const GAME_VERSION='0.6.0'")
s = s.replace("LAST_CHANGE='Detección L/R sin regex + smoke test automático en Chromium'", "LAST_CHANGE='Traductor per-hueso: ejes + offset de pose aprendido con idle/run Hunyuan'")

debug_old = "h+='<div>roles RUN comunes: brazos '+r.armPairs+' · piernas '+r.legPairs+'</div>';if(r.arms)h+='<div>brazos: <b>'+esc(r.arms.label)+'</b> · pistas '+r.arms.tracks+' · score '+Number(r.arms.score).toFixed(3)+'</div>';if(r.legs)h+='<div>piernas: <b>'+esc(r.legs.label)+'</b> · pistas '+r.legs.tracks+' · score '+Number(r.legs.score).toFixed(3)+'</div>';"
debug_new = "h+='<div>roles RUN comunes: brazos '+r.armPairs+' · piernas '+r.legPairs+'</div>';h+='<div>perfiles por hueso: <b>'+r.profileCount+'</b></div>';if(r.profileSummary)h+='<div style=\"opacity:.85\">'+esc(r.profileSummary)+'</div>';"
s = s.replace(debug_old, debug_new)

a = s.find('function clipPairData(')
b = s.find('function sameRigCount(', a)
if a < 0 or b < 0:
    raise SystemExit('No encontré bloque de calibración para reemplazar')

new_cal = r'''function rolePairData(srcClip,nativeClip,r,N=32){const Amap=roleTrackMap(srcClip),Bmap=roleTrackMap(nativeClip),a=Amap.get(r),n=Bmap.get(r);if(!a||!n)return null;const A=velocitySeq(a,N),B=velocitySeq(n,N),ra=Math.sqrt(A.reduce((s,v)=>s+v.lengthSq(),0)/N),rb=Math.sqrt(B.reduce((s,v)=>s+v.lengthSq(),0)/N);if(ra<1e-5||rb<1e-5)return null;return{role:r,a,n,A:A.map(v=>v.clone().multiplyScalar(1/ra)),B:B.map(v=>v.clone().multiplyScalar(1/rb))}}
function bestRoleScore(row,basis,N=32){if(!row)return{score:0,shift:0};let best=1e9,bestShift=0;for(let sh=0;sh<N;sh++){let sum=0;for(let i=0;i<N;i++)sum+=mapV(row.A[i],basis).distanceToSquared(row.B[(i+sh)%N]);const sc=sum/N;if(sc<best){best=sc;bestShift=sh}}return{score:best,shift:bestShift}}
function basisAbs(q,qr,p){const invr=qr.clone().invert(),qbi=p.q.clone().invert(),d=invr.multiply(q.clone()).normalize(),d2=p.q.clone().multiply(d).multiply(qbi).normalize();return qr.clone().multiply(d2).normalize()}
function calibrateRole(rawRun,nativeRun,rawIdle,nativeIdle,r,qr,N=32){const run=rolePairData(rawRun,nativeRun,r,N);if(!run)return null;const idle=rolePairData(rawIdle,nativeIdle,r,N);let best=null;for(const base of AXIS_BASES){const sr=bestRoleScore(run,base,N),si=idle?bestRoleScore(idle,base,N):{score:0,shift:0},score=sr.score+si.score*.12;if(!best||score<best.score)best={...base,score,runShift:sr.shift,idleShift:si.shift}}
const rawIdleMap=roleTrackMap(rawIdle),nativeIdleMap=roleTrackMap(nativeIdle),rawRunMap=roleTrackMap(rawRun),nativeRunMap=roleTrackMap(nativeRun);let qa,qn;if(rawIdleMap.has(r)&&nativeIdleMap.has(r)){qa=qAt(rawIdleMap.get(r),0);qn=qAt(nativeIdleMap.get(r),0)}else{qa=qAt(rawRunMap.get(r),0);qn=qAt(nativeRunMap.get(r),best.runShift/N)}const aligned=basisAbs(qa,qr,best),corr=qn.clone().multiply(aligned.clone().invert()).normalize();best.corr=corr;best.role=r;return best}
function calibrateProfiles(rawRun,nativeRun,rawIdle,nativeIdle,bones,restQ){const A=roleTrackMap(rawRun),B=roleTrackMap(nativeRun),out={};for(const r of A.keys()){if(!B.has(r)||!groupForRole(r))continue;const bone=bones.find(x=>role(x.name)===r),qr=bone&&restQ.get(bone.name);if(!qr)continue;const p=calibrateRole(rawRun,nativeRun,rawIdle,nativeIdle,r,qr);if(p)out[r]=p}return out}
function transformClip(src,profiles,bones,restQ){const c=src.clone(),roleToBone=new Map();for(const b of bones){const r=role(b.name);if(r&&!roleToBone.has(r))roleToBone.set(r,b)}for(const tr of c.tracks){if(!/quaternion$/i.test(tr.name))continue;const r=trackRole(tr),p=profiles[r],b=roleToBone.get(r);if(!p||!b)continue;const qr=restQ.get(b.name);if(!qr)continue;const q=new THREE.Quaternion();for(let i=0;i<tr.values.length;i+=4){q.fromArray(tr.values,i).normalize();const tmp=basisAbs(q,qr,p),out=p.corr.clone().multiply(tmp).normalize();out.toArray(tr.values,i)}}return c}
'''
s = s[:a] + new_cal + s[b:]

a = s.find("html=html.replace(/new GLTFLoader")
b = s.find("html=html.replace('const roomId", a)
if a < 0 or b < 0:
    raise SystemExit('No encontré bloque loader para reemplazar')

loader = r'''html=html.replace(/new GLTFLoader\(\)\.load\('\.\.\/fightermp\/Barbarian\.glb',g=>\{source=g\.scene;clips=g\.animations\|\|\[\];mkClips\(\);player=avatar\(\);player\.x=-11;player\.z=-11;play\(player,'idle'\);document\.getElementById\('splash'\)\.style\.display='none'\},undefined,e=>fatal\(e\?\.message\|\|e\)\)/,`Promise.all([new Promise((res,rej)=>new FBXLoader().load('main_rigged.fbx',res,undefined,rej)),new Promise((res,rej)=>new FBXLoader().load('../main_idle.fbx',res,undefined,rej)),new Promise((res,rej)=>new FBXLoader().load('../main_run.fbx',res,undefined,rej)),new Promise((res,rej)=>new GLTFLoader().load('../fightermp/Barbarian.glb',res,undefined,rej))]).then(([fbx,nIdle,nRun,g])=>{source=fbx;const ts=findSkin(fbx),ss=findSkin(g.scene),is=findSkin(nIdle),rs=findSkin(nRun),bm=makeBoneMap(ts,ss),hip=(ss?.skeleton?.bones||[]).find(b=>role(b.name)==='hips')?.name||'mixamorigHips',bones=ts?.skeleton?.bones||[],restQ=new Map();ts?.skeleton?.pose();for(const b of bones)restQ.set(b.name,b.quaternion.clone());const raw=[];if(ts&&ss)for(const c of(g.animations||[])){try{const rc=SkeletonUtils.retargetClip(ts,ss,c,{names:bm,hip,preserveBoneMatrix:true,preserveBonePositions:true,useTargetMatrix:true});rc.name=c.name;raw.push(rc)}catch(e){console.warn('retarget',c.name,e)}}const rawRun=raw.find(c=>/running[_ ]?a|\\brun\\b|sprint/i.test(c.name))||raw.find(c=>/run/i.test(c.name)),rawIdle=raw.find(c=>/idle|stand/i.test(c.name)),nativeRun=nRun.animations?.[0]||null,nativeIdle=nIdle.animations?.[0]||null,rawRunMap=roleTrackMap(rawRun),nativeRunMap=roleTrackMap(nativeRun),armPairs=[...rawRunMap.keys()].filter(r=>groupForRole(r)==='arms'&&nativeRunMap.has(r)).length,legPairs=[...rawRunMap.keys()].filter(r=>groupForRole(r)==='legs'&&nativeRunMap.has(r)).length,profiles=calibrateProfiles(rawRun,nativeRun,rawIdle,nativeIdle,bones,restQ),profileCount=Object.keys(profiles).length,calibrated=profileCount>=6;clips=calibrated?raw.map(c=>transformClip(c,profiles,bones,restQ)):raw;const profileSummary=Object.entries(profiles).map(([r,p])=>r+': '+p.label+' · '+p.score.toFixed(2)).join(' | ');window.__bomber3dRetarget={calibrated,ok:!!clips.length,mapped:Object.keys(bm).length,targetBones:bones.length,sourceBones:ss?.skeleton?.bones?.length||0,sourceClips:g.animations?.length||0,retargeted:clips.length,nativeIdleClips:nIdle.animations?.length||0,nativeRunClips:nRun.animations?.length||0,refMatched:Math.min(sameRigCount(ts,is),sameRigCount(ts,rs)),rawRunQ:[...(rawRun?.tracks||[])].filter(t=>/quaternion$/i.test(t.name)).length,nativeRunQ:[...(nativeRun?.tracks||[])].filter(t=>/quaternion$/i.test(t.name)).length,armPairs,legPairs,profileCount,profileSummary,rawRoles:[...rawRunMap.keys()].join(','),nativeRoles:[...nativeRunMap.keys()].join(',')};mkClips();player=avatar();player.x=-11;player.z=-11;play(player,'idle');document.getElementById('splash').style.display='none'}).catch(e=>fatal(e?.message||e))`);
'''
s = s[:a] + loader + s[b:]

p.write_text(s, encoding='utf-8')
print('Applied Bomber3D v0.6.0 per-bone calibration')
