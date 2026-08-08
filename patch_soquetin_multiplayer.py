from pathlib import Path
from urllib.request import urlopen, Request
import re

SOURCE='https://raw.githubusercontent.com/mateofoulkes-lab/Soquetin/main/index.html'
ASSET='https://mateofoulkes-lab.github.io/Soquetin/'
req=Request(SOURCE,headers={'User-Agent':'Mozilla/5.0'})
s=urlopen(req,timeout=30).read().decode('utf-8')

# This file lives in tools, so point Soquetin's external assets back to the canonical game repo.
assets=[
  'sock puppet 3d model.glb','death.mp3','jump1.mp3','pop.mp3','walk-compress.mp3','walk-expand.mp3',
  'AFICHE-01.JPG','AFICHE-02.JPG','AFICHE-03.JPG','AFICHE-04.JPG','AFICHE-05.JPG'
]
for name in assets:
    url=ASSET+name.replace(' ','%20')
    s=s.replace("'"+name+"'", "'"+url+"'")
    s=s.replace('"'+name+'"', '"'+url+'"')

s=s.replace('<title>El Enigma de Soquetin — Enhanced</title>','<title>Soquetin · prueba multiplayer P2P</title>',1)
s=s.replace('<title>El Enigma de Soquetin</title>','<title>Soquetin · prueba multiplayer P2P</title>',1)
s=s.replace('CARGANDO ENHANCED · 0%','CARGANDO MULTIPLAYER · 0%',1)

# Multiplayer HUD.
css='''\n    #mpHud{position:fixed;left:12px;bottom:12px;z-index:70;pointer-events:none;padding:8px 10px;border-radius:9px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(5px);font:700 10px ui-monospace,monospace;color:#eee7d6;line-height:1.45}\n    #mpHud .ok{color:#a9f3ad} #mpHud .wait{color:#ffd88a}\n'''
if '</style>' not in s: raise SystemExit('style close not found')
s=s.replace('</style>',css+'  </style>',1)

hud='''\n  <div id="mpHud"><div><span class="wait" id="mpState">P2P · CONECTANDO…</span></div><div id="mpPeers">JUGADORES · 1</div><div id="mpPing">RTT · — ms</div></div>\n'''
anchor='<div id="blackFade"></div>'
if anchor not in s: raise SystemExit('blackFade markup anchor not found')
s=s.replace(anchor,anchor+hud,1)

# Trystero: decentralized discovery + direct WebRTC data channels.
imp="    import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';"
if imp not in s: raise SystemExit('KTX2 import anchor not found')
s=s.replace(imp,imp+"\n    import { joinRoom, selfId } from 'https://esm.sh/trystero@0.25.3';",1)

# Keep a processed clone of the local GLB for remote peers.
loader_anchor="    gltfLoader.setKTX2Loader(ktx2Loader);"
if loader_anchor not in s: raise SystemExit('loader anchor missing')
s=s.replace(loader_anchor,loader_anchor+"\n    let multiplayerAvatarTemplate=null;",1)
add_model="      tiltRoot.add(model);"
if add_model not in s: raise SystemExit('local model add anchor missing')
s=s.replace(add_model,add_model+"\n      multiplayerAvatarTemplate=model.clone(true);\n      upgradeRemoteAvatars();",1)

# Insert multiplayer implementation immediately after player state is declared.
p0=s.find('    const P={')
if p0<0: raise SystemExit('P state start not found')
p1=s.find('\n    };',p0)
if p1<0: raise SystemExit('P state end not found')
p1 += len('\n    };')

mp=r'''

    // ------------------------------------------------------------
    // MULTIPLAYER PROBE — P2P WebRTC, one shared test space.
    // Networking is visual-only: remote players never enter local collision/support logic.
    // ------------------------------------------------------------
    const mpState=document.getElementById('mpState');
    const mpPeers=document.getElementById('mpPeers');
    const mpPing=document.getElementById('mpPing');
    const remotePlayers=new Map();
    const MP_ROOM_ID='soquetin-global-test-v1';
    const mpRoom=joinRoom({appId:'soquetin-multiplayer-probe-2026'},MP_ROOM_ID,{
      onJoinError:({error})=>{
        console.warn('Multiplayer join error',error);
        if(mpState){mpState.textContent='P2P · ERROR';mpState.className='';}
      }
    });
    const poseAction=mpRoom.makeAction('pose-v1');
    let mpSendAccumulator=0, mpPingAccumulator=0;

    function setRemoteVisual(r){
      while(r.visual.children.length){r.visual.remove(r.visual.children[0]);}
      if(multiplayerAvatarTemplate){
        const clone=multiplayerAvatarTemplate.clone(true);
        clone.traverse(o=>{
          if(o.isMesh){
            o.castShadow=true;
            o.receiveShadow=false;
            const mats=Array.isArray(o.material)?o.material:[o.material];
            const cloned=mats.map(m=>m?.clone?m.clone():m);
            o.material=Array.isArray(o.material)?cloned:cloned[0];
          }
        });
        r.visual.add(clone);
        r.hasRealModel=true;
      }else{
        const m=new THREE.MeshStandardMaterial({color:0xc7b78c,roughness:.82,emissive:0x17130d,emissiveIntensity:.25});
        const body=new THREE.Mesh(new THREE.BoxGeometry(.42,.88,.38),m);
        body.position.y=.44; body.castShadow=true; r.visual.add(body);
        r.hasRealModel=false;
      }
    }

    function makeRemotePlayer(peerId){
      if(remotePlayers.has(peerId)) return remotePlayers.get(peerId);
      const root=new THREE.Group();
      const visual=new THREE.Group(); root.add(visual); scene.add(root);
      root.position.copy(P.pos); root.rotation.y=P.yaw;
      const r={peerId,root,visual,hasRealModel:false,targetPos:P.pos.clone(),targetYaw:P.yaw,targetScale:new THREE.Vector3(1,1,1),targetTilt:0,targetTiltY:0,targetTiltZ:0,lastPacket:performance.now()};
      setRemoteVisual(r);
      remotePlayers.set(peerId,r);
      refreshMpHud();
      return r;
    }

    function removeRemotePlayer(peerId){
      const r=remotePlayers.get(peerId); if(!r)return;
      scene.remove(r.root);
      r.root.traverse(o=>{
        if(o.isMesh && o.material){
          const mats=Array.isArray(o.material)?o.material:[o.material];
          for(const m of mats) if(m && m!==wallMat && m.dispose) m.dispose();
        }
      });
      remotePlayers.delete(peerId);
      refreshMpHud();
    }

    function upgradeRemoteAvatars(){
      if(!multiplayerAvatarTemplate)return;
      for(const r of remotePlayers.values()) if(!r.hasRealModel) setRemoteVisual(r);
    }

    function currentPose(){
      return {
        x:P.pos.x,y:P.pos.y,z:P.pos.z,yaw:P.yaw,
        sx:visualRoot.scale.x,sy:visualRoot.scale.y,sz:visualRoot.scale.z,
        tilt:tiltRoot.rotation.x,ty:tiltRoot.position.y,tz:tiltRoot.position.z,
        dead:P.dead?1:0,t:performance.now()
      };
    }

    function refreshMpHud(){
      const n=1+remotePlayers.size;
      if(mpPeers) mpPeers.textContent=`JUGADORES · ${n}`;
      if(mpState){mpState.textContent=remotePlayers.size?'P2P · CONECTADO':'P2P · ESPERANDO PEERS';mpState.className=remotePlayers.size?'ok':'wait';}
    }

    mpRoom.onPeerJoin=peerId=>{
      makeRemotePlayer(peerId);
      poseAction.send(currentPose(),{target:peerId}).catch(()=>{});
      refreshMpHud();
    };
    mpRoom.onPeerLeave=peerId=>removeRemotePlayer(peerId);
    poseAction.onMessage=(d,{peerId})=>{
      if(!d || typeof d.x!=='number')return;
      const r=makeRemotePlayer(peerId);
      r.targetPos.set(d.x,d.y,d.z);
      r.targetYaw=Number.isFinite(d.yaw)?d.yaw:r.targetYaw;
      r.targetScale.set(Number.isFinite(d.sx)?d.sx:1,Number.isFinite(d.sy)?d.sy:1,Number.isFinite(d.sz)?d.sz:1);
      r.targetTilt=Number.isFinite(d.tilt)?d.tilt:0;
      r.targetTiltY=Number.isFinite(d.ty)?d.ty:0;
      r.targetTiltZ=Number.isFinite(d.tz)?d.tz:0;
      r.root.visible=!d.dead;
      r.lastPacket=performance.now();
    };

    function lerpAngle(a,b,t){
      let d=(b-a+Math.PI)%(Math.PI*2)-Math.PI;
      if(d<-Math.PI)d+=Math.PI*2;
      return a+d*t;
    }

    function updateMultiplayer(dt){
      mpSendAccumulator+=dt;
      // 20 Hz snapshots; visual interpolation happens every rendered frame.
      if(mpSendAccumulator>=.05){
        mpSendAccumulator%=.05;
        poseAction.send(currentPose()).catch(()=>{});
      }
      const k=1-Math.exp(-dt*18);
      for(const r of remotePlayers.values()){
        r.root.position.lerp(r.targetPos,k);
        r.root.rotation.y=lerpAngle(r.root.rotation.y,r.targetYaw,k);
        r.visual.scale.lerp(r.targetScale,k);
        r.visual.rotation.x=THREE.MathUtils.lerp(r.visual.rotation.x,r.targetTilt,k);
        r.visual.position.y=THREE.MathUtils.lerp(r.visual.position.y,r.targetTiltY,k);
        r.visual.position.z=THREE.MathUtils.lerp(r.visual.position.z,r.targetTiltZ,k);
      }
      mpPingAccumulator+=dt;
      if(mpPingAccumulator>=2.5){
        mpPingAccumulator=0;
        const ids=[...remotePlayers.keys()];
        if(!ids.length){if(mpPing)mpPing.textContent='RTT · — ms';}
        else Promise.allSettled(ids.map(id=>mpRoom.ping(id))).then(rs=>{
          const vals=rs.filter(r=>r.status==='fulfilled'&&Number.isFinite(r.value)).map(r=>r.value);
          if(mpPing)mpPing.textContent=vals.length?`RTT · ${Math.round(vals.reduce((a,b)=>a+b,0)/vals.length)} ms`:'RTT · — ms';
        });
      }
    }

    refreshMpHud();
    console.log('Soquetin multiplayer P2P', {selfId, room:MP_ROOM_ID});
'''
s=s[:p1]+mp+s[p1:]

# Update multiplayer once per frame, immediately before rendering.
render_anchor='      renderer.render(scene,camera);'
if render_anchor not in s: raise SystemExit('render anchor missing')
s=s.replace(render_anchor,'      updateMultiplayer(dt);\n'+render_anchor,1)

# Make the on-screen title explicitly identify this as a test if that element exists.
s=s.replace('El Enigma de Soquetin</div>','El Enigma de Soquetin · MULTIPLAYER TEST</div>',1)

# Basic build sanity checks.
for required in ['joinRoom','makeAction(\'pose-v1\')','updateMultiplayer(dt)','mpRoom.ping','remotePlayers','multiplayerAvatarTemplate']:
    if required not in s: raise SystemExit('missing multiplayer feature: '+required)
for rel in assets:
    if ("'"+rel+"'") in s or ('"'+rel+'"') in s: raise SystemExit('relative asset remains: '+rel)

Path('multiplayer.html').write_text(s,encoding='utf-8')
print('built multiplayer.html',len(s))
