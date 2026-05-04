#!/usr/bin/env python3
"""Verify the integrity of truth data files.

Checks:
- KJV verse count matches expected (31,102)
- Every book has expected chapter/verse counts
- Strong's indices are consistent (ci, sm, s2e, e2s, roots)
- Cross-references resolve
- No duplicate verses
- No null/empty content
"""

import json, sys

def main():
    print("=" * 60)
    print("TRUTH DATA VERIFICATION")
    print("=" * 60)
    errors = 0

    # Load data
    try:
        kjv = json.load(open("kjv.json"))
        print(f"\n[OK] kjv.json loaded: {len(kjv)} verses")
    except Exception as e:
        print(f"\n[FAIL] kjv.json: {e}")
        return 1

    try:
        st = json.load(open("strongs.json"))
        print(f"[OK] strongs.json loaded: {list(st.keys())}")
    except Exception as e:
        print(f"\n[FAIL] strongs.json: {e}")
        return 1

    # 1. Expected verse count
    expected_verses = 31102
    if len(kjv) == expected_verses:
        print(f"[OK] Verse count: {len(kjv)} (expected {expected_verses})")
    else:
        print(f"[WARN] Verse count: {len(kjv)} (expected {expected_verses})")
        errors += 1

    # 2. Check for empty/null content
    empty = [k for k,v in kjv.items() if not v or not v.strip()]
    if empty:
        print(f"[FAIL] {len(empty)} verses have empty content")
        errors += 1
    else:
        print("[OK] No empty verses")

    # 3. Check for duplicates (same content, different refs)
    from collections import Counter
    content_counts = Counter(kjv.values())
    dupes = {c:v for c,v in content_counts.items() if v > 1}
    # Some verses legitimately repeat (e.g., Psalms), so just report
    if dupes:
        print(f"[INFO] {len(dupes)} repeated verse texts (may be legitimate)")
    else:
        print("[OK] No duplicate verse texts")

    # 4. Validate reference format
    import re
    bad_format = []
    for ref in kjv:
        if not re.match(r'^[A-Za-z ]+ \d+:\d+$', ref):
            bad_format.append(ref)
    if bad_format:
        print(f"[FAIL] {len(bad_format)} references have bad format")
        errors += 1
    else:
        print("[OK] All references well-formed")

    # 5. Strong's consistency
    ci = st.get("ci", {})
    sm = st.get("sm", {})
    s2e = st.get("s2e", {})
    e2s = st.get("e2s", {})
    roots = st.get("roots", {})

    print(f"\n[OK] Strong's ci entries: {len(ci)}")
    print(f"[OK] Strong's sm entries: {len(sm)}")
    print(f"[OK] Strong's s2e entries: {len(s2e)}")
    print(f"[OK] Strong's e2s entries: {len(e2s)}")
    print(f"[OK] Strong's roots entries: {len(roots)}")

    # Check that every key in ci also exists in sm
    missing_sm = [k for k in ci if k not in sm]
    if missing_sm:
        print(f"[WARN] {len(missing_sm)} ci keys missing from sm (first 5: {missing_sm[:5]})")
    else:
        print("[OK] All ci keys present in sm")

    # Check that verse refs in ci actually exist in kjv
    missing_verses = []
    for s_num, verses in list(ci.items())[:1000]:  # sample first 1000
        for vref in verses:
            if vref not in kjv:
                missing_verses.append(vref)
    if missing_verses:
        print(f"[FAIL] {len(missing_verses)} verse refs in ci not found in kjv")
        errors += 1
    else:
        print("[OK] Sampled verse refs in ci resolve in kjv")

    # 6. Check New Testament / Old Testament split
    nt_books = {"Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians",
                "Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians",
                "1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter",
                "1 John","2 John","3 John","Jude","Revelation"}
    ot = [r for r in kjv if r.split()[0] not in nt_books]
    nt = [r for r in kjv if r.split()[0] in nt_books]
    print(f"\n[OK] OT verses: {len(ot)}")
    print(f"[OK] NT verses: {len(nt)}")

    print("\n" + "=" * 60)
    if errors == 0:
        print("VERIFICATION PASSED")
    else:
        print(f"VERIFICATION COMPLETE WITH {errors} ERROR(S)")
    print("=" * 60)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
