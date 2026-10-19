"""vault の原本から、公開用の index.html（図解）と text.html（文字だけの版）を作る。
使い方: python -I tools/build.py <原本HTMLのパス>
必要: Google Chrome（JSで組み立てる表やグラフの中身を書き出すため）、beautifulsoup4（text.html 用）
"""
import sys, re, subprocess, tempfile, os, pathlib

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
root = pathlib.Path(__file__).resolve().parent.parent
src = open(sys.argv[1], encoding="utf-8").read()
head_end = src.index("</style>") + len("</style>")

# 1) index.html：原本を doctype/head で包むだけ（見た目と操作は原本どおり）
index = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
         '<meta name="robots" content="noindex,nofollow">\n'
         '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
         'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n'
         + src[:head_end] + "\n</head>\n<body>\n" + src[head_end:] + "\n</body>\n</html>\n")
(root / "index.html").write_text(index, encoding="utf-8")

# 2) JS 実行後の DOM を書き出す。業種パネルは5つとも出すように差し替える
s = src
old = s[s.index('    panel.innerHTML=`<div class="panel-head fade">'):s.index('  seg.addEventListener("keydown"')]
s = s.replace(old, '''    panel.querySelectorAll(".ipanel").forEach((p,j)=>p.hidden=j!==i);
  }
  panel.innerHTML=IND.map((d,i)=>`<div class="ipanel" data-i="${i}"><div class="panel-head">${ico(d.k,"lg")}<div class="body"><span class="pill ${d.verdict[0]}">${d.verdict[1]}</span><h3 style="margin-top:6px">${d.full}</h3><p class="small">${d.tag}</p></div></div>
      <div class="kv">${d.items.map((it,j)=>`<div><span class="n">${String(j+1).padStart(2,"0")}</span>${it[0]}</div><div>${it[1]}</div>`).join("")}</div></div>`).join("");
''', 1)
s = s.replace("show(cur);\n})();", "})();", 1)
with tempfile.TemporaryDirectory() as td:
    w = os.path.join(td, "w.html")
    open(w, "w", encoding="utf-8").write('<!doctype html><html lang="ja"><head><meta charset="utf-8"></head><body>' + s + "</body></html>")
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom", "file://" + w],
                         capture_output=True, text=True, check=True).stdout
    full = os.path.join(td, "full.html")
    open(full, "w", encoding="utf-8").write(dom)
    # 3) text.html：見出し・表・箇条書きだけの版
    subprocess.run([sys.executable, "-I", str(root / "tools" / "to_text.py"), full, str(root / "text.html")], check=True)
print("built index.html and text.html")
