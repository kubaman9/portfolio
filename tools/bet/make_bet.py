#!/usr/bin/env python3
"""Build the password-gated /bet dashboard.

Reads the dashboard_template's html_shell (doctype through </html>, containing
the literal token __ARCHIVE_JSON__) and an archive JSON file, substitutes the
data in, encrypts the whole resulting page with AES-256-GCM (key derived via
PBKDF2-HMAC-SHA256, 250000 iterations, from BET_PAGE_PASSPHRASE), and writes a
small self-contained password-gate wrapper around the ciphertext to bet/index.html.

This script needs no database credentials: it only touches the template file,
the archive JSON file, and the environment variable BET_PAGE_PASSPHRASE.

Usage:
  BET_PAGE_PASSPHRASE=... python3 make_bet.py --template shell.html --archive archive.json --out bet/index.html
"""
import argparse
import base64
import json
import os
import re
import sys

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256
    import Crypto.Random
except ImportError:
    print("FATAL: pycryptodome is required (pip install pycryptodome)", file=sys.stderr)
    sys.exit(1)

PLACEHOLDER = "__ARCHIVE_JSON__"
PBKDF2_ITERATIONS = 250000
MIN_OUTPUT_BYTES = 20 * 1024  # a build that collapses to ~1KB (empty archive) must fail loud

WRAPPER_TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Ledger</title>
<style>:root{{color-scheme:light dark}}body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b1220;color:#e6ebf5;font:16px system-ui,sans-serif}}
form{{width:min(320px,86vw)}}h1{{font-size:18px;font-weight:600;margin:0 0 14px}}input,button{{width:100%;box-sizing:border-box;padding:12px;border-radius:8px;border:1px solid #33415c;font:inherit;margin-bottom:10px}}
input{{background:#111a2e;color:inherit}}button{{background:#c9922a;color:#111;border:0;font-weight:600;cursor:pointer}}#e{{color:#f08a7c;min-height:1.2em;font-size:14px}}</style></head>
<body><form id="f"><h1>Ledger</h1><input id="p" type="password" placeholder="Password" autocomplete="current-password" autofocus><button>Open</button><div id="e"></div></form>
<script>(function(){{var S="{salt_b64}",I="{iv_b64}",C="{ct_b64}",N={iterations};
function d(s){{return Uint8Array.from(atob(s),function(c){{return c.charCodeAt(0);}});}}
async function open(pw){{var k=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveKey"]);
k=await crypto.subtle.deriveKey({{name:"PBKDF2",salt:d(S),iterations:N,hash:"SHA-256"}},k,{{name:"AES-GCM",length:256}},false,["decrypt"]);
var pt=await crypto.subtle.decrypt({{name:"AES-GCM",iv:d(I)}},k,d(C));return new TextDecoder().decode(pt);}}
function go(h){{document.open();document.write(h);document.close();}}
var e=document.getElementById("e");
document.getElementById("f").addEventListener("submit",function(ev){{ev.preventDefault();e.textContent="";
open(document.getElementById("p").value).then(function(h){{try{{sessionStorage.setItem("bp",document.getElementById("p").value);}}catch(x){{}}go(h);}}).catch(function(){{e.textContent="Wrong password";}});}});
try{{var s=sessionStorage.getItem("bp");if(s)open(s).then(go).catch(function(){{}});}}catch(x){{}}
}})();</script></body></html>"""


def encrypt(plaintext: str, passphrase: str) -> tuple[str, str, str]:
    salt = Crypto.Random.get_random_bytes(16)
    iv = Crypto.Random.get_random_bytes(12)
    key = PBKDF2(passphrase, salt, dkLen=32, count=PBKDF2_ITERATIONS, hmac_hash_module=SHA256)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    # Web Crypto's AES-GCM decrypt expects ciphertext||tag concatenated, matching
    # what SubtleCrypto.encrypt itself would have produced.
    combined = ciphertext + tag
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return b64(salt), b64(iv), b64(combined)


def fail(msg: str) -> None:
    print(f"\nBUILD REFUSED: {msg}\n", file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="path to the html_shell file (contains __ARCHIVE_JSON__)")
    ap.add_argument("--archive", required=True, help="path to the archive JSON file (index + days)")
    ap.add_argument("--out", required=True, help="output path, e.g. bet/index.html")
    args = ap.parse_args()

    passphrase = os.environ.get("BET_PAGE_PASSPHRASE")
    if not passphrase:
        fail("BET_PAGE_PASSPHRASE is not set in the environment. Refusing to build with no passphrase or a default.")

    shell = open(args.template, encoding="utf-8").read()
    if PLACEHOLDER not in shell:
        fail(f"template does not contain the {PLACEHOLDER} placeholder — wrong file, or it was already substituted once")

    archive_raw = open(args.archive, encoding="utf-8").read()
    try:
        archive = json.loads(archive_raw)
    except json.JSONDecodeError as e:
        fail(f"archive JSON does not parse: {e}")

    if "index" not in archive or "days" not in archive:
        fail("archive JSON is missing 'index' or 'days' — wrong shape")
    if not archive["days"]:
        fail("archive JSON has zero days — refusing to publish an empty archive")

    # Substitute. json.dumps output never contains a literal </script>, but guard
    # anyway since this string is about to be embedded inside a <script> tag pre-encryption.
    archive_json_str = json.dumps(archive, ensure_ascii=False, separators=(",", ":"))
    archive_json_str = archive_json_str.replace("</script", "<\\/script")
    plaintext = shell.replace(PLACEHOLDER, archive_json_str, 1)

    if PLACEHOLDER in plaintext:
        fail("__ARCHIVE_JSON__ still present after substitution — substitution did not fully take, the data never went in")

    # Grep the pre-encryption plaintext for a known real value as a sanity check
    # that the archive actually is the real one and not an empty/placeholder stub.
    sample_date = sorted(archive["days"].keys())[-1]
    sample_matchup = None
    for p in archive["days"][sample_date].get("picks", []):
        if p.get("matchup"):
            sample_matchup = p["matchup"]
            break
    if sample_matchup and sample_matchup not in plaintext:
        fail(f"a known matchup ({sample_matchup!r}) from the archive is not present in the substituted page — substitution is suspect")

    salt_b64, iv_b64, ct_b64 = encrypt(plaintext, passphrase)

    output = WRAPPER_TEMPLATE.format(
        salt_b64=salt_b64, iv_b64=iv_b64, ct_b64=ct_b64, iterations=PBKDF2_ITERATIONS
    )

    # ---- Safety checks on the FINAL output file, before it ever touches disk for real ----
    size = len(output.encode("utf-8"))
    if size <= MIN_OUTPUT_BYTES:
        fail(f"output is only {size} bytes (<= {MIN_OUTPUT_BYTES}) — looks like a broken/empty build, not a real archive")

    if 'type="password"' not in output or 'id="f"' not in output:
        fail("password form is missing from the output")

    if f'C="{ct_b64}"' not in output or len(ct_b64) < 1000:
        fail("ciphertext blob is missing or suspiciously short in the output")

    if PLACEHOLDER in output:
        fail(f"{PLACEHOLDER} literally present in the final output — the data never went in")

    # The whole point of the gate: nothing outside the ciphertext may reveal any
    # real data. Strip the ciphertext value and grep what's left.
    outside_ct = output.replace(ct_b64, "")
    lower_outside = outside_ct.lower()
    if "units" in lower_outside:
        fail("the literal word 'units' appears outside the ciphertext — plaintext data leak")
    for date, doc in archive["days"].items():
        for p in doc.get("picks", []) or []:
            matchup = p.get("matchup") or ""
            for team_word in re.findall(r"[A-Z][a-zA-Z']{3,}", matchup):
                if team_word in outside_ct:
                    fail(f"a plaintext team/name token ({team_word!r}, from {date}) appears outside the ciphertext — plaintext data leak")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"OK: wrote {args.out} ({size} bytes), {len(archive['days'])} archived days, latest={archive['index'].get('latest_day')}")


if __name__ == "__main__":
    main()
