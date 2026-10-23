import urllib.request, urllib.error, re, json, os, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
os.makedirs("out", exist_ok=True)
log = []

def get(url, accept="text/html,*/*;q=0.8", referer=None):
    h = {"User-Agent": UA, "Accept": accept, "Accept-Language": "en-US,en;q=0.9"}
    if referer:
        h["Referer"] = referer
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, repr(e)

def save(name, text):
    with open(f"out/{name}", "w") as f:
        f.write(text)

BUY = "https://www.apple.com/shop/buy-iphone/iphone-duo"
st, hd, body = get(BUY)
log.append(f"buy page: {st} len={len(body)}")
save("buy.html", body)
slugs = sorted(set(re.findall(r"/shop/buy-iphone/iphone-duo/[a-z0-9\-]+", body)))
save("slugs.txt", "\n".join(slugs))
parts = []
ctx = {}
for m in re.finditer(r"\b[A-Z0-9]{4,6}(?:LL|AM|LZ)/A\b", body):
    p = m.group(0)
    if p not in ctx:
        parts.append(p)
        ctx[p] = body[max(0, m.start() - 300): m.end() + 300]
save("parts.txt", "\n".join(parts))
save("parts_context.txt", "\n\n=====\n\n".join(f"{p}\n{c}" for p, c in ctx.items()))
log.append(f"slugs={len(slugs)} parts={len(parts)}")
for key in ["fulfillment", "cppart", "pickup", "PRODUCT_SELECTION_BOOTSTRAP", "carrierPolicy"]:
    idx = [m.start() for m in re.finditer(key, body)][:5]
    log.append(f"key {key}: {len(idx)} hits")
    save(f"key_{key}.txt", "\n\n-----\n\n".join(body[max(0, i - 400): i + 600] for i in idx))

if slugs:
    st2, _, b2 = get("https://www.apple.com" + slugs[0])
    log.append(f"slug page {slugs[0]}: {st2} len={len(b2)}")
    save("slug.html", b2)
    more = []
    for m in re.finditer(r"\b[A-Z0-9]{4,6}(?:LL|AM|LZ)/A\b", b2):
        if m.group(0) not in parts and m.group(0) not in more:
            more.append(m.group(0))
    log.append(f"extra parts on slug page: {more[:20]}")
    parts += more

tests = []
if parts:
    p = parts[0]
    base = "https://www.apple.com/shop/fulfillment-messages"
    tests = [
        f"{base}?fae=true&pl=true&mts.0=regular&mts.1=compact&parts.0={p}&searchNearby=true&store=R074",
        f"{base}?pl=true&mts.0=regular&parts.0={p}&location=33431",
        f"{base}?pl=true&mts.0=regular&cppart=UNLOCKED/US&parts.0={p}&location=33431",
        f"{base}?pl=true&mts.0=regular&cppart=VERIZON/US&parts.0={p}&location=33431",
        base + "?pl=true&mts.0=regular&location=33431&" + "&".join(f"parts.{i}={q}" for i, q in enumerate(parts[:8])),
    ]
for i, u in enumerate(tests):
    st, hd, b = get(u, accept="application/json, text/plain, */*", referer=BUY)
    log.append(f"fulfillment test {i}: {st} len={len(b)} type={hd.get('Content-Type')} url={u}")
    save(f"fm_{i}.json", b[:200000])
    time.sleep(2)

save("log.txt", "\n".join(log))
print("\n".join(log))
