#!/usr/bin/env python3
import os, re, json, glob, html
LIB = "C:/Users/YOU/ObsidianVault/Beauty Library"
OUTS = ["C:/Users/YOU/ObsidianVault/_BeautyLibrarian/Beauty-Lookbook.html",
        "C:/Users/YOU/Documents/Beauty-Lookbook.html"]
def scalar(fm,k):
    m=re.search(r'^'+k+r':\s*(.*)$',fm,re.M); 
    return (m.group(1).strip().strip('"') if m else "")
def listf(fm,k):
    m=re.search(r'^'+k+r':\s*\[(.*)\]\s*$',fm,re.M)
    return [x.strip().strip('"') for x in m.group(1).split(",") if x.strip()] if m else []
cards=[]
for f in sorted(glob.glob(os.path.join(LIB,"*.md")), key=os.path.getmtime, reverse=True):
    s=open(f,encoding='utf-8').read()
    if not s.startswith("---"): continue
    fm=s.split("---",2)[1]
    cards.append({"title":scalar(fm,"title") or os.path.basename(f)[:-3],
        "category":scalar(fm,"category") or "other","thumb":scalar(fm,"thumbnail"),
        "url":scalar(fm,"source_url"),"tags":listf(fm,"tags")})
data=json.dumps(cards,ensure_ascii=False)
H='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beauty Lookbook</title><style>
:root{--bg:#fbf7f4;--card:#fff;--ink:#2c2430;--accent:#b5667e;--soft:#efe3ea;--line:#e7ddd7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,Segoe UI,Roboto,sans-serif}
.top{position:sticky;top:0;background:var(--bg);padding:12px;border-bottom:1px solid var(--line);z-index:5}
h1{margin:0 0 8px;font-size:1.2rem}#q{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:10px;font-size:1rem}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.chip{background:var(--soft);border:none;border-radius:999px;padding:6px 12px;font-size:.85rem;cursor:pointer}
.chip.on{background:var(--accent);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:12px}
.c{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column}
.c img{width:100%;aspect-ratio:3/4;object-fit:cover;background:var(--soft)}
.c .b{padding:8px}.c .t{font-size:.85rem;font-weight:600;line-height:1.25;margin-bottom:4px}
.c .tg{font-size:.7rem;color:#8a7f87;line-height:1.3}
.cat{display:inline-block;font-size:.62rem;text-transform:uppercase;letter-spacing:.04em;background:var(--soft);border-radius:4px;padding:1px 5px;margin-bottom:4px}
.count{color:#8a7f87;font-size:.8rem;margin:0 12px}
</style></head><body>
<div class="top"><h1>💄 Beauty Lookbook</h1>
<input id="q" placeholder="Search tags, category, title… (e.g. hijab quick)">
<div class="chips" id="chips"></div></div>
<div class="count" id="count"></div><div class="grid" id="grid"></div>
<script>
const D=__DATA__;
const cats=["all",...[...new Set(D.map(c=>c.category))].sort()];
const chips=document.getElementById("chips");let active="all";
cats.forEach(c=>{const b=document.createElement("button");b.className="chip"+(c==="all"?" on":"");b.textContent=c;b.onclick=()=>{active=c;[...chips.children].forEach(x=>x.classList.toggle("on",x.textContent===c));render()};chips.appendChild(b)});
const grid=document.getElementById("grid"),count=document.getElementById("count"),q=document.getElementById("q");
function render(){const term=q.value.toLowerCase().split(/\\s+/).filter(Boolean);
 const r=D.filter(c=>{if(active!=="all"&&c.category!==active)return false;
  const hay=(c.title+" "+c.category+" "+c.tags.join(" ")).toLowerCase();
  return term.every(t=>hay.includes(t));});
 count.textContent=r.length+" look"+(r.length===1?"":"s");
 grid.innerHTML=r.map(c=>`<a class="c" href="${c.url||'#'}" target="_blank" rel="noopener">`+
  `<img loading="lazy" src="${c.thumb||''}" alt="">`+
  `<div class="b"><span class="cat">${c.category}</span><div class="t">${c.title}</div>`+
  `<div class="tg">${c.tags.slice(0,8).join(" · ")}</div></div></a>`).join("");}
q.addEventListener("input",render);render();
</script></body></html>'''
def adapt(thumb, out):
    if not thumb: return ""
    if thumb.startswith("http"): return thumb
    if "/_BeautyLibrarian/" in out:
        return thumb[len("_BeautyLibrarian/"):] if thumb.startswith("_BeautyLibrarian/") else thumb
    return "file:///C:/Users/YOU/ObsidianVault/" + thumb
for o in OUTS:
    cards_o=[dict(c, thumb=adapt(c["thumb"], o)) for c in cards]
    data2=json.dumps(cards_o,ensure_ascii=False)
    Ho=H.replace("__DATA__",data2)
    os.makedirs(os.path.dirname(o),exist_ok=True); open(o,"w",encoding="utf-8").write(Ho)
print("gallery built with",len(cards),"cards ->",", ".join(OUTS))
