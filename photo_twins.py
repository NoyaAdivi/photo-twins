"""
photo_twins.py - Find exact and near-duplicate photos in a big collection.
A companion to sort-photos: run it on your whole library or on Sorted/photos.

Two kinds of twins:
    exact    - byte-for-byte identical files (same size, same SHA-256)
    similar  - the same picture saved again: resized, re-compressed, sent over
               WhatsApp, a slightly different crop (perceptual dHash + BK-tree)

Nothing is ever deleted. By default the script only writes a report.
With --move-to, the extra copies are moved to a separate folder and every move
is logged, so --undo can put everything back exactly where it was.

Usage examples (Windows):
    python photo_twins.py "D:\\Pictures"
    python photo_twins.py "D:\\Pictures" --similar
    python photo_twins.py "D:\\Pictures" --similar --move-to "D:\\Duplicates"
    python photo_twins.py --undo "D:\\Duplicates\\moves.csv"
"""

import argparse
import base64
import csv
import hashlib
import html
import io
import os
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageOps

try:  # HEIC/HEIF support is optional
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

try:  # progress bar is optional
    from tqdm import tqdm
except ImportError:
    def tqdm(it, **_):
        return it

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif", ".heic", ".heif"}
CHUNK = 1 << 20  # 1 MB


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@dataclass
class Photo:
    path: Path
    size: int
    mtime: float
    sha256: str = ""
    dhash: int = -1
    width: int = 0
    height: int = 0
    error: str = ""

    @property
    def pixels(self):
        return self.width * self.height


@dataclass
class Group:
    kind: str                      # "exact" or "similar"
    photos: list
    keeper: Photo = None
    distance: dict = field(default_factory=dict)  # path -> Hamming distance to keeper


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------
def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def dhash(img, size=8):
    """Difference hash: shrink to (size+1) x size grayscale and compare each
    pixel with its right neighbour. Survives resizing, re-compression and small
    colour changes. Returns a size*size bit integer."""
    small = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = small.tobytes()  # one byte per pixel in "L" mode
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (left > right)
    return bits


def hamming(a, b):
    return (a ^ b).bit_count()


def load_visual(photo):
    """Fill width, height and dhash. Applies EXIF rotation first, so a rotated
    copy of the same photo still matches."""
    try:
        with Image.open(photo.path) as im:
            w, h = im.size
            if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):  # rotated 90 degrees
                w, h = h, w
            photo.width, photo.height = w, h
            im.draft("RGB", (64, 64))  # fast JPEG decoding at reduced size
            photo.dhash = dhash(ImageOps.exif_transpose(im))
    except Exception as e:  # corrupt or unsupported file
        photo.error = f"{type(e).__name__}: {e}"
    return photo


# ---------------------------------------------------------------------------
# BK-tree: finds all hashes within a Hamming radius without comparing every pair
# ---------------------------------------------------------------------------
class BKTree:
    def __init__(self):
        self.root = None  # node = [value, item, {distance: child}]

    def add(self, value, item):
        if self.root is None:
            self.root = [value, item, {}]
            return
        node = self.root
        while True:
            d = hamming(value, node[0])
            child = node[2].get(d)
            if child is None:
                node[2][d] = [value, item, {}]
                return
            node = child

    def search(self, value, radius):
        found, stack = [], [self.root] if self.root else []
        while stack:
            node = stack.pop()
            d = hamming(value, node[0])
            if d <= radius:
                found.append((d, node[1]))
            for dist, child in node[2].items():
                if d - radius <= dist <= d + radius:
                    stack.append(child)
        return found


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def scan(src, skip=None):
    photos = []
    skip = skip.resolve() if skip else None
    for root, dirs, files in os.walk(src):
        if skip and Path(root).resolve() == skip:
            dirs[:] = []
            continue
        for name in files:
            p = Path(root) / name
            if p.suffix.lower() in IMAGE_EXTS:
                st = p.stat()
                photos.append(Photo(p, st.st_size, st.st_mtime))
    return photos


def pick_keeper(photos):
    """Keep the best copy: most pixels, then biggest file, then oldest,
    then the shortest path (usually the 'original' folder)."""
    return max(photos, key=lambda p: (p.pixels, p.size, -p.mtime, -len(str(p.path))))


def find_exact(photos, workers):
    by_size = defaultdict(list)
    for p in photos:
        by_size[p.size].append(p)
    candidates = [p for same in by_size.values() if len(same) > 1 for p in same]

    def work(p):
        try:
            p.sha256 = file_sha256(p.path)
        except OSError as e:
            p.error = str(e)
        return p

    with ThreadPoolExecutor(workers) as ex:
        list(tqdm(ex.map(work, candidates), total=len(candidates), desc="Exact", unit="img"))

    by_hash = defaultdict(list)
    for p in candidates:
        if p.sha256:
            by_hash[p.sha256].append(p)
    return [Group("exact", g) for g in by_hash.values() if len(g) > 1]


def find_similar(photos, radius, workers):
    with ThreadPoolExecutor(workers) as ex:
        list(tqdm(ex.map(load_visual, photos), total=len(photos), desc="Similar", unit="img"))
    ok = [p for p in photos if p.dhash >= 0]

    # Greedy clustering around the best copies: the highest-quality photo
    # becomes a centre and takes every free photo within the radius. Unlike
    # union-find this never chains A~B~C into one group when A and C differ.
    ok.sort(key=lambda p: (p.pixels, p.size), reverse=True)
    tree = BKTree()
    for i, p in enumerate(ok):
        tree.add(p.dhash, i)
    taken = [False] * len(ok)
    clusters = []
    for i, p in enumerate(ok):
        if taken[i]:
            continue
        taken[i] = True
        members = [p]
        for _, j in sorted(tree.search(p.dhash, radius)):
            if not taken[j]:
                taken[j] = True
                members.append(ok[j])
        clusters.append(members)
    return [Group("similar", g) for g in clusters if len(g) > 1]


def build_groups(photos, similar, radius, workers):
    groups = find_exact(photos, workers)
    if similar:
        # one representative per exact group, so a file is never in two groups
        in_exact = {id(p) for g in groups for p in g.photos}
        reps = [p for p in photos if id(p) not in in_exact] + [g.photos[0] for g in groups]
        sim = find_similar(reps, radius, workers)
        # merge exact groups into the similar group of their representative
        rep_of = {id(g.photos[0]): g for g in groups}
        merged = []
        for sg in sim:
            members = []
            for p in sg.photos:
                eg = rep_of.pop(id(p), None)
                members.extend(eg.photos if eg else [p])
            merged.append(Group("similar", members))
        groups = list(rep_of.values()) + merged
    for g in groups:
        for p in g.photos:
            if p.dhash < 0 and not p.error:
                load_visual(p)
        g.keeper = pick_keeper(g.photos)
        if g.keeper.dhash >= 0:
            g.distance = {str(p.path): hamming(p.dhash, g.keeper.dhash)
                          for p in g.photos if p.dhash >= 0}
    groups.sort(key=lambda g: -sum(p.size for p in g.photos if p is not g.keeper))
    return groups


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def write_csv(groups, out):
    path = out / "duplicates.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["group", "kind", "role", "path", "bytes", "width", "height", "distance"])
        for i, g in enumerate(groups, 1):
            for p in sorted(g.photos, key=lambda p: p is not g.keeper):
                w.writerow([i, g.kind, "keep" if p is g.keeper else "duplicate", str(p.path),
                            p.size, p.width, p.height, g.distance.get(str(p.path), 0)])
    return path


def thumb(path, size=220):
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((size, size))
            buf = io.BytesIO()
            im.convert("RGB").save(buf, "JPEG", quality=72)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


HTML_HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Photo Twins report</title>
<style>
:root{--ink:#2B2140;--muted:#7A6B88;--peach:#FFE6DE;--lav:#E8E4FF;--mint:#D9F3E7;--coral:#E36E57;--violet:#6F60F0}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--ink);
background:linear-gradient(135deg,var(--peach),var(--lav) 55%,var(--mint));background-attachment:fixed;min-height:100vh}
header{text-align:center;padding:48px 16px 24px}h1{margin:0;font-size:56px;font-weight:800;
background:linear-gradient(90deg,var(--coral),var(--violet));-webkit-background-clip:text;color:transparent;animation:rise .8s ease-out both}
.sub{color:var(--muted);font-size:20px;margin-top:8px}.stats{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin:26px 0 8px}
.stat{background:#fff9;backdrop-filter:blur(6px);border-radius:20px;padding:14px 22px;min-width:150px;animation:rise .8s ease-out both}
.stat b{display:block;font-size:30px}.stat span{color:var(--muted);font-size:14px}
main{max-width:1200px;margin:0 auto;padding:12px 16px 60px}
.group{background:#ffffffb3;border-radius:26px;padding:18px 20px;margin:18px 0;box-shadow:0 8px 30px #6f60f014;animation:rise .6s ease-out both}
.group h2{font-size:17px;margin:0 0 12px;display:flex;gap:10px;align-items:center}
.pill{font-size:12px;padding:4px 12px;border-radius:99px;font-weight:700}.exact{background:var(--mint);color:#1F7350}.similar{background:var(--lav);color:#5548C8}
.row{display:flex;gap:14px;overflow-x:auto;padding-bottom:6px}
.card{flex:0 0 200px;background:#fff;border-radius:18px;padding:8px;border:2px solid transparent;transition:transform .25s}
.card:hover{transform:translateY(-6px) rotate(-1deg)}.card.keep{border-color:#8FD6BB}
.card img{width:100%;height:150px;object-fit:cover;border-radius:12px;background:var(--lav)}
.tag{font-size:12px;font-weight:800;margin:6px 2px 2px}.keep .tag{color:#1F7350}.dup .tag{color:var(--coral)}
.meta{font-size:12px;color:var(--muted);word-break:break-all;margin:2px}
@keyframes rise{from{opacity:0;transform:translateY(16px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body>"""


def write_html(groups, out, total, max_groups):
    extra = [p for g in groups for p in g.photos if p is not g.keeper]
    saved = sum(p.size for p in extra)
    parts = [HTML_HEAD, "<header><h1>Photo Twins</h1><div class='sub'>Every group keeps one copy. Nothing was deleted.</div>",
             "<div class='stats'>"]
    for value, label in ((f"{total:,}", "photos scanned"), (f"{len(groups):,}", "twin groups"),
                         (f"{len(extra):,}", "extra copies"), (human(saved), "you can free")):
        parts.append(f"<div class='stat'><b>{value}</b><span>{label}</span></div>")
    parts.append("</div></header><main>")
    for i, g in enumerate(tqdm(groups[:max_groups], desc="Report", unit="group"), 1):
        parts.append(f"<section class='group'><h2>Group {i} <span class='pill {g.kind}'>{g.kind}</span></h2><div class='row'>")
        for p in sorted(g.photos, key=lambda p: p is not g.keeper):
            keep = p is g.keeper
            d = g.distance.get(str(p.path))
            dist = "" if keep or d is None else f" · distance {d}"
            parts.append(
                f"<div class='card {'keep' if keep else 'dup'}'><img loading='lazy' src='{thumb(p.path)}' alt=''>"
                f"<div class='tag'>{'✓ KEEP' if keep else 'DUPLICATE'}</div>"
                f"<div class='meta'>{p.width}×{p.height} · {human(p.size)}{dist}</div>"
                f"<div class='meta'>{html.escape(str(p.path))}</div></div>")
        parts.append("</div></section>")
    if len(groups) > max_groups:
        parts.append(f"<p class='sub' style='text-align:center'>+ {len(groups) - max_groups:,} more groups in duplicates.csv</p>")
    parts.append("</main></body></html>")
    path = out / "report.html"
    path.write_text("".join(parts), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Move and undo
# ---------------------------------------------------------------------------
def unique_target(target):
    n, base = 1, target
    while target.exists():
        target = base.with_name(f"{base.stem} ({n}){base.suffix}")
        n += 1
    return target


def move_duplicates(groups, src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    log = dst / "moves.csv"
    new = not log.exists()
    moved = 0
    with open(log, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["original", "moved_to"])
        for g in groups:
            for p in g.photos:
                if p is g.keeper or not p.path.exists():
                    continue
                target = unique_target(dst / p.path.relative_to(src))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p.path), str(target))
                w.writerow([str(p.path), str(target)])
                moved += 1
    return moved, log


def undo(log):
    with open(log, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    restored = 0
    for row in reversed(rows):
        src, back = Path(row["moved_to"]), Path(row["original"])
        if src.exists() and not back.exists():
            back.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(back))
            restored += 1
    log.rename(log.with_suffix(".undone.csv"))
    return restored, len(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Find exact and near-duplicate photos. Never deletes anything.")
    p.add_argument("src", nargs="?", help="Folder with the images (scanned recursively)")
    p.add_argument("--similar", action="store_true", help="Also find near-duplicates (resized, re-saved, rotated)")
    p.add_argument("--distance", type=int, default=6,
                   help="Max Hamming distance for 'similar', 0-64 (default 6, lower is stricter)")
    p.add_argument("--report", default="twins-report", help="Folder for report.html and duplicates.csv")
    p.add_argument("--move-to", help="Move the extra copies here (logged in moves.csv)")
    p.add_argument("--undo", metavar="MOVES_CSV", help="Put back every file listed in a moves.csv")
    p.add_argument("--max-groups", type=int, default=500, help="Groups shown in report.html (default 500)")
    p.add_argument("--workers", type=int, default=0, help="Threads for reading files (default: CPU cores)")
    args = p.parse_args(argv)
    if not args.undo and not args.src:
        p.error("give a source folder, or --undo MOVES_CSV")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.undo:
        restored, total = undo(Path(args.undo))
        print(f"Restored {restored} of {total} files.")
        return 0

    src = Path(args.src).resolve()
    if not src.is_dir():
        sys.exit(f"Not a folder: {src}")
    dst = Path(args.move_to).resolve() if args.move_to else None
    if dst and dst == src:
        sys.exit("--move-to must be a different folder than the source")
    workers = args.workers or os.cpu_count() or 4

    photos = scan(src, skip=dst)
    print(f"Found {len(photos):,} images in {src}")
    groups = build_groups(photos, args.similar, args.distance, workers)

    out = Path(args.report).resolve()
    out.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv(groups, out)
    html_path = write_html(groups, out, len(photos), args.max_groups)
    extra = sum(len(g.photos) - 1 for g in groups)
    saved = sum(p.size for g in groups for p in g.photos if p is not g.keeper)
    print(f"{len(groups):,} groups, {extra:,} extra copies, {human(saved)} can be freed")
    print(f"Report: {html_path}\nCSV:    {csv_path}")

    if dst:
        moved, log = move_duplicates(groups, src, dst)
        print(f"Moved {moved:,} files to {dst}\nUndo with: python photo_twins.py --undo \"{log}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
