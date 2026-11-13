import csv
from pathlib import Path

from PIL import Image, ImageDraw

import photo_twins as pt


def make_photo(path, size=(400, 300), seed=0, quality=95):
    img = Image.new("RGB", size, (240, 230, 250))
    d = ImageDraw.Draw(img)
    for i in range(6):
        x = (seed * 37 + i * 61) % size[0]
        y = (seed * 53 + i * 41) % size[1]
        d.ellipse([x, y, x + size[0] // 4, y + size[1] // 4], fill=((seed * 70 + i * 40) % 255, 120, 200))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=quality)
    return path


def test_hamming_and_dhash_stable_under_resize(tmp_path):
    a = make_photo(tmp_path / "a.jpg")
    b = tmp_path / "b.jpg"
    Image.open(a).resize((200, 150)).save(b, quality=60)
    ha = pt.dhash(Image.open(a))
    hb = pt.dhash(Image.open(b))
    assert pt.hamming(ha, hb) <= 6
    assert pt.hamming(0b1011, 0b0001) == 2


def test_bktree_matches_bruteforce():
    import random
    rnd = random.Random(1)
    values = [rnd.getrandbits(64) for _ in range(300)]
    tree = pt.BKTree()
    for i, v in enumerate(values):
        tree.add(v, i)
    q = values[5] ^ 0b111
    got = sorted(i for _, i in tree.search(q, 10))
    want = sorted(i for i, v in enumerate(values) if pt.hamming(q, v) <= 10)
    assert got == want and 5 in got


def test_exact_and_similar_groups(tmp_path):
    src = tmp_path / "pics"
    orig = make_photo(src / "trip" / "beach.jpg", seed=1)
    (src / "backup").mkdir()
    (src / "backup" / "beach.jpg").write_bytes(orig.read_bytes())          # exact twin
    Image.open(orig).resize((200, 150)).save(src / "whatsapp.jpg", quality=50)  # similar twin
    make_photo(src / "other.jpg", seed=9)                                   # unrelated

    photos = pt.scan(src)
    exact_only = pt.build_groups(photos, similar=False, radius=6, workers=2)
    assert len(exact_only) == 1 and exact_only[0].kind == "exact"

    groups = pt.build_groups(pt.scan(src), similar=True, radius=6, workers=2)
    assert len(groups) == 1
    names = sorted(p.path.name for p in groups[0].photos)
    assert names == ["beach.jpg", "beach.jpg", "whatsapp.jpg"]
    assert groups[0].keeper.width == 400  # the full-size copy is kept


def test_move_and_undo_roundtrip(tmp_path):
    src = tmp_path / "pics"
    a = make_photo(src / "a.jpg", seed=2)
    (src / "copy").mkdir()
    (src / "copy" / "a.jpg").write_bytes(a.read_bytes())
    dst = tmp_path / "dups"

    assert pt.main([str(src), "--move-to", str(dst), "--report", str(tmp_path / "r")]) == 0
    assert len(list(src.rglob("*.jpg"))) == 1
    rows = list(csv.reader(open(tmp_path / "r" / "duplicates.csv", encoding="utf-8-sig")))
    assert rows[0][:3] == ["group", "kind", "role"] and len(rows) == 3
    assert (tmp_path / "r" / "report.html").read_text(encoding="utf-8").count("DUPLICATE") == 1

    assert pt.main(["--undo", str(dst / "moves.csv")]) == 0
    assert len(list(src.rglob("*.jpg"))) == 2


def test_keeper_prefers_more_pixels():
    small = pt.Photo(Path("s.jpg"), 900, 1, width=100, height=100)
    big = pt.Photo(Path("b.jpg"), 500, 2, width=800, height=600)
    assert pt.pick_keeper([small, big]) is big
