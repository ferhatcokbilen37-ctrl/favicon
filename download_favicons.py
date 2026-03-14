"""
Spor & Casino Favicon İndirici
-------------------------------
Kullanım:
  pip install requests
  python download_favicons.py

Yaklaşık 500-1000 favicon indirir (bazı domainler favicon döndürmez).
Sonuçlar ./favicons/ klasörüne kaydedilir.
"""

import requests
import os
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from domains import DOMAINS

# ── Ayarlar ──────────────────────────────────────────────────────────────────
OUTPUT_DIR   = Path("favicons")
LOG_FILE     = Path("download_log.json")
SIZE         = 64          # favicon boyutu (16, 32, 64, 128)
WORKERS      = 10          # paralel indirme sayısı
DELAY        = 0.05        # istek arası bekleme (saniye)
MIN_BYTES    = 200         # bu değerin altındaki dosyalar sahte/boş sayılır
TIMEOUT      = 8           # istek zaman aşımı

APIS = [
    lambda d: f"https://www.google.com/s2/favicons?domain={d}&sz={SIZE}",
    lambda d: f"https://icons.duckduckgo.com/ip3/{d}.ico",
    lambda d: f"https://logo.clearbit.com/{d}",
]
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (favicon-collector/1.0)"})

log = {"ok": [], "fail": []}


def safe_name(domain: str) -> str:
    return domain.replace(".", "_").replace("/", "_")


def try_download(domain: str) -> tuple[bool, str]:
    """Sırayla API'leri dene, ilk başarılı olanı kaydet."""
    for api in APIS:
        url = api(domain)
        try:
            r = session.get(url, timeout=TIMEOUT)
            if r.status_code == 200 and len(r.content) >= MIN_BYTES:
                # İçerik tipi belirle
                ct = r.headers.get("content-type", "")
                ext = ".ico" if "ico" in ct else ".png"
                out_path = OUTPUT_DIR / f"{safe_name(domain)}{ext}"
                out_path.write_bytes(r.content)
                return True, url
        except Exception:
            continue
        finally:
            time.sleep(DELAY)
    return False, ""


def process(domain: str, idx: int, total: int):
    ok, url = try_download(domain)
    status = "✓" if ok else "✗"
    print(f"[{idx:>4}/{total}] {status}  {domain}")
    if ok:
        log["ok"].append(domain)
    else:
        log["fail"].append(domain)


def main():
    domains = DOMAINS
    total   = len(domains)
    print(f"\n{'─'*50}")
    print(f"  {total} domain için favicon indiriliyor")
    print(f"  Klasör : {OUTPUT_DIR.resolve()}")
    print(f"{'─'*50}\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as exe:
        futs = {exe.submit(process, d, i+1, total): d
                for i, d in enumerate(domains)}
        for f in as_completed(futs):
            f.result()

    LOG_FILE.write_text(json.dumps(log, indent=2, ensure_ascii=False))

    print(f"\n{'─'*50}")
    print(f"  Başarılı : {len(log['ok'])}")
    print(f"  Başarısız: {len(log['fail'])}")
    print(f"  Log      : {LOG_FILE.resolve()}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    main()
