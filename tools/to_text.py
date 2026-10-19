"""図解HTML（全部の文字を書き込んだ版）から、AIが読みやすい文字だけのHTMLを作る。
使い方: python to_text.py <static_out.html> <text.html>
"""
import sys, re, html
from bs4 import BeautifulSoup, NavigableString, Tag

src, dst = sys.argv[1], sys.argv[2]
soup = BeautifulSoup(open(src, encoding="utf-8").read(), "html.parser")
for t in soup.select("svg, style, script, nav, .axis, .gridlines, .ref, .thumb, link, meta, .short"):
    t.decompose()

out = []
esc = html.escape


def txt(el):
    if el is None:
        return ""
    s = el.get_text(" ", strip=True) if isinstance(el, Tag) else str(el)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" 推定", "（推定）").replace("推定 。", "（推定）。")
    return s


def P(s):
    if s:
        out.append(f"<p>{esc(s)}</p>")


def UL(items, ordered=False):
    items = [i for i in items if i]
    if items:
        tag = "ol" if ordered else "ul"
        out.append(f"<{tag}>" + "".join(f"<li>{esc(i)}</li>" for i in items) + f"</{tag}>")


def TABLE(head, rows):
    h = "".join(f"<th>{esc(c)}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    out.append(f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>")


def cls(el):
    return el.get("class", []) if isinstance(el, Tag) else []


def level(td):
    dots = td.select_one(".dots")
    if td.select_one(".q"):
        return "データなし"
    dl = td.select_one(".dl")
    if dl:
        return txt(dl)
    if dots:
        c = cls(dots)
        return {"l3": "強い", "l2": "中くらい", "l1": "弱い"}.get(next((x for x in c if x.startswith("l")), ""), "")
    return txt(td)


def walk(el):
    for ch in el.children:
        if isinstance(ch, NavigableString):
            continue
        handle(ch)


def handle(el):
    c = cls(el)
    name = el.name
    if name in ("h1", "h2", "h3"):
        out.append(f"<{name}>{esc(txt(el))}</{name}>")
        return
    if "eyebrow" in c:
        out.append(f"<p><strong>{esc(txt(el))}</strong></p>")
        return
    if name == "p" or "legend" in c and False:
        P(txt(el))
        return
    if "legend" in c:
        P("凡例：" + txt(el))
        return
    if "tile" in c:
        parts = [txt(el.select_one(".pill")), txt(el.select_one(".k")), txt(el.select_one(".v")), txt(el.select_one(".small")), txt(el.select_one(".d"))]
        P("・" + "｜".join(p for p in parts if p))
        return
    if "bars" in c:
        rows = []
        kids = [k for k in el.children if isinstance(k, Tag)]
        for i in range(0, len(kids) - 1, 2):
            lab, tr = kids[i], kids[i + 1]
            if not txt(lab) and not txt(tr):
                continue
            rows.append([txt(lab), txt(tr)])
        if rows:
            TABLE(["項目", "値"], rows)
        return
    if "ipanel" in c:
        head = el.select_one(".panel-head")
        out.append(f"<h3>{esc(txt(head.select_one('h3')))}</h3>")
        P(f"判定：{txt(head.select_one('.pill'))}。{txt(head.select_one('p'))}")
        cells = [k for k in el.select_one(".kv").children if isinstance(k, Tag)]
        TABLE(["項目", "内容"], [[txt(cells[i]), txt(cells[i + 1])] for i in range(0, len(cells), 2)])
        return
    if "seg" in c:
        return
    if name == "table":
        ths = [txt(th) for th in el.select("thead th")]
        rows, grp = [], ""
        for tr in el.select("tbody tr"):
            if "grp" in cls(tr):
                grp = txt(tr)
                continue
            first = txt(tr.find(["th", "td"]))
            vals = [level(td) for td in tr.find_all("td")]
            rows.append(([grp] if grp else []) + [first] + vals)
        has_grp = any(len(r) > len(ths) for r in rows)
        TABLE((["区分"] if has_grp else []) + ths, rows)
        return
    if "hrow" in c:
        P(f"{txt(el.select_one('.hn'))}：{txt(el.select_one('.t'))} → 判定「{txt(el.select_one('.pill'))}」。{txt(el.select_one('.s'))}")
        return
    if "qa" in c:
        cells = [k for k in el.children if isinstance(k, Tag)]
        hd = [txt(k) for k in cells if "hd" in cls(k)]
        body = [k for k in cells if "hd" not in cls(k)]
        TABLE(hd or ["項目", "内容"], [[txt(body[i]), txt(body[i + 1])] for i in range(0, len(body) - 1, 2)])
        return
    if "rk-head" in c:
        return
    if "rk" in c:
        ps = el.find_all("p", recursive=False)
        out.append(f"<h3>{esc(txt(el.select_one('.rk-t')))}</h3>")
        P("調査で分かったこと：" + txt(ps[0]))
        P("事業責任者が決めること・確認すること：" + txt(ps[1]))
        return
    if "abc" in c:
        P("・" + "｜".join(x for x in [txt(el.select_one('.tag')), txt(el.find('b')), txt(el.select_one('p.small')), txt(el.select_one('.how'))] if x))
        return
    if "conds" in c:
        UL([txt(k) for k in el.children if isinstance(k, Tag)])
        return
    if "rank" in c:
        P(f"{txt(el.select_one('.no'))}. {txt(el.find('h3'))}：{txt(el.find('p'))}")
        return
    if "flow7" in c:
        UL([txt(li) for li in el.find_all("li")], ordered=True)
        return
    if "slots" in c:
        P("ヒアリングの枠：浄化槽・産廃・消防・設備資材卸・ビルメンの5業種それぞれで、小（〜9人）・中（10〜29人）・大（30人〜）を1社ずつ、計15社。")
        return
    if "layers" in c:
        P("営業で見せる顔：" + "／".join(txt(k) for k in el.select(".lay-col")))
        P("裏側で共通にするAI：" + "／".join(txt(k) for k in el.select(".lay-bar span")))
        return
    if "bld" in c:
        P("1つの建物に来る書類：" + "／".join(txt(k) for k in el.select(".doc")) + "。" + txt(el.select_one(".bld-cap")))
        P("流れ：点検会社 → " + " → ".join(txt(k) for k in el.select(".bld-node")))
        return
    if "fork" in c:
        P("空いた1時間（AIで減った作業）の行き先：")
        UL([txt(k) for k in el.select(".dstc")])
        return
    if name == "details":
        out.append(f"<h3>{esc(txt(el.find('summary')))}</h3>")
        P(txt(el.select_one(".inner")))
        return
    if "src-list" in c:
        out.append("<ul>" + "".join(f'<li><a href="{esc(a["href"])}">{esc(txt(a))}</a></li>' for a in el.find_all("a")) + "</ul>")
        return
    if any(k in c for k in ("row", "dstc", "msg", "rev", "callout", "core", "chip", "step")) or name in ("footer",):
        P(txt(el))
        return
    if name in ("div", "section", "header", "main", "ul", "ol", "li", "span", "a", "b", "i", "strong"):
        if name == "div" and not any(isinstance(k, Tag) for k in el.children):
            P(txt(el))
            return
        walk(el)
        return
    P(txt(el))


title = txt(soup.find("title")) or "5業種AI事業の検証"
for t in soup.select("title"):
    t.decompose()
walk(soup.select_one("main") or soup)

page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{esc(title)}（文字だけの版）</title>
<style>body{{max-width:860px;margin:0 auto;padding:24px 16px 64px;font:16px/1.7 -apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;color:#1d1d1f;background:#fff}}h1{{font-size:1.8rem;line-height:1.3}}h2{{margin-top:2.4em;border-top:1px solid #ddd;padding-top:1em}}table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}}th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}}th{{background:#f2f2f7}}.note{{background:#f2f2f7;padding:12px 14px;border-radius:8px;font-size:14px}}</style>
</head>
<body>
<p class="note">このページは、図解ページ（<a href="./">https://kinopy0918.github.io/vertical-ai-market-research/</a>）と同じ内容を、AIや読み上げソフトが読みやすいように文字だけにしたものです。表の「強い／中くらい／弱い／データなし」は図解の点の数と同じです。「（推定）」はFOXの計算・推論、それ以外は出典つきの事実です。</p>
{chr(10).join(out)}
</body>
</html>
"""
open(dst, "w", encoding="utf-8").write(page)
print(len(out), "blocks")
