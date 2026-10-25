"""Download the trained perception models for the three supported kitchens from Hugging Face.

    python scripts/download_weights.py                     # all kitchens: FloorPlan1, FloorPlan15, FloorPlan17
    python scripts/download_weights.py --kitchen FloorPlan1
    python scripts/download_weights.py --list              # show what would be fetched, download nothing

Each kitchen has a primary detector (YOLO26s, every frame), a look-alike specialist (YOLO26m, only while the agent
holds an object) and seven object-state classifiers. Files land in sim/weights/v3/, where the console looks for them,
and every file is checked against the SHA256SUMS published next to it. The models are released by the MISE project:
https://huggingface.co/ArashNasr
"""
import argparse
import hashlib
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "sim", "weights", "v3")
REPO = "ArashNasr/ai2thor-kitchen-perception-{}"
KITCHENS = ("FloorPlan1", "FloorPlan15", "FloorPlan17")
KINDS = ("yolo26s", "amb26m", "state_broken", "state_cooked", "state_dirty", "state_filled", "state_on", "state_open",
         "state_sliced")


def url(kitchen, name):
    return f"https://huggingface.co/{REPO.format(kitchen.lower())}/resolve/main/{name}"


def sums(kitchen):
    with urllib.request.urlopen(url(kitchen, "SHA256SUMS"), timeout=60) as r:
        lines = r.read().decode("utf-8").splitlines()
    return {ln.split()[1]: ln.split()[0] for ln in lines if len(ln.split()) == 2}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(kitchen, name, expected):
    out = os.path.join(DEST, name)
    if os.path.isfile(out) and sha256(out) == expected:
        print(f"  ok (already here)  {name}")
        return
    tmp = out + ".part"
    try:
        from huggingface_hub import hf_hub_download            # resumable, cached; optional
        got = hf_hub_download(REPO.format(kitchen.lower()), name)
        with open(got, "rb") as src, open(tmp, "wb") as dst:
            dst.write(src.read())
    except ImportError:
        urllib.request.urlretrieve(url(kitchen, name), tmp)
    if sha256(tmp) != expected:
        os.remove(tmp)
        sys.exit(f"checksum mismatch for {name}: download it again")
    os.replace(tmp, out)
    print(f"  downloaded         {name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--kitchen", choices=KITCHENS, action="append", help="repeatable; default: all three")
    ap.add_argument("--list", action="store_true", help="print the files and their URLs, download nothing")
    a = ap.parse_args()
    os.makedirs(DEST, exist_ok=True)
    for k in a.kitchen or KITCHENS:
        print(f"{k}  ({REPO.format(k.lower())})")
        table = sums(k)
        for kind in KINDS:
            name = f"{k}.{kind}.pt"
            if name not in table:
                print(f"  missing upstream   {name}")
                continue
            if a.list:
                print(f"  {name}  {url(k, name)}")
            else:
                fetch(k, name, table[name])
    if not a.list:
        print(f"done: weights in {os.path.relpath(DEST, ROOT)}")


if __name__ == "__main__":
    main()
