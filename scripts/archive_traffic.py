#!/usr/bin/env python3
"""Archive GitHub's rolling traffic windows to a private repo. Python stdlib only."""
import base64, datetime as dt, json, os, sys, time, urllib.error, urllib.request
TOKEN=os.environ["TRAFFIC_TOKEN"]
OWNER=os.environ.get("TRAFFIC_OWNER","mateofoulkes-lab")
DEST=os.environ.get("TRAFFIC_DATA_REPO","repo-traffic-data")
API="https://api.github.com"
def req(method,path,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"traffic-archiver"}
    if data is not None:headers["Content-Type"]="application/json"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(API+path,headers=headers,data=data,method=method),timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403,429,500,502,503) and attempt<3:
                print("Retry",e.code,path,flush=True);time.sleep(2**attempt*3);continue
            raise RuntimeError(f"{method} {path}: HTTP {e.code}: {e.read().decode()[:350]}") from e
def listing():
    page=1
    while True:
        items=req("GET",f"/user/repos?affiliation=owner&per_page=100&page={page}")
        if not items:break
        for item in items:
            if item["owner"]["login"].lower()==OWNER.lower() and item["name"]!=DEST:
                yield item
        if len(items)<100:break
        page+=1
def main():
    path=f"/repos/{OWNER}/{DEST}/contents/traffic.json"
    sha=None
    try:
        stored=req("GET",path)
        sha=stored["sha"]
        history=json.loads(base64.b64decode(stored["content"]).decode())
    except RuntimeError as e:
        if "HTTP 404" not in str(e):raise
        history={"schema":1,"repos":{}}
    history.setdefault("repos",{})
    ok=0;errors=[]
    for repository in listing():
        name=repository["name"]
        entry=history["repos"].setdefault(name,{"name":name,"days":{}})
        entry["private"]=repository["private"]
        success=True
        for metric in ("views","clones"):
            try:
                result=req("GET",f"/repos/{OWNER}/{name}/traffic/{metric}?per=day")
                for item in result.get(metric,[]):
                    date=item["timestamp"][:10]
                    entry["days"].setdefault(date,{})[metric]={"count":item["count"],"uniques":item["uniques"]}
            except Exception as e:
                success=False;errors.append(f"{name}/{metric}: {e}")
        if success:ok+=1
    if ok==0:
        raise RuntimeError("Ningún repositorio accesible: revisá permisos del token. "+"; ".join(errors[:3]))
    history["updated_at"]=dt.datetime.now(dt.timezone.utc).isoformat()
    body={"message":"Archive repository traffic "+dt.date.today().isoformat(),"content":base64.b64encode((json.dumps(history,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()).decode()}
    if sha:body["sha"]=sha
    req("PUT",path,body)
    print(f"Guardados {ok} repositorios. Errores: {len(errors)}")
    for error in errors:print("WARN",error)
    if errors:sys.exit(1)
if __name__=="__main__":main()
