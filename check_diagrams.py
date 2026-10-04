"""Structural checks for the diagrams that have a property worth asserting.

Run it from the repository root, with no arguments:

    python check_diagrams.py

Three things are checked, each of which degrades quietly if nobody looks:

  1. THE SSD IS A BLACK BOX. 11_system_sequence_diagram must have exactly one
     system lifeline, every message must touch it, every use case it cites must
     exist in 01_use_case_diagram, and every actor on it must be an actor there.
     An SSD that grows an internal object has silently become a design sequence
     diagram, which is what 12 to 18 already are.

  2. THE DESIGN SEQUENCE DIAGRAMS ARE NOT SSDs. 12 to 18 must each show at
     least one internal lifeline. These seven were once deleted on the strength
     of their names, on the assumption they were SSDs; they are not, and the
     supervisor's artifact list asks for both kinds.

  3. THE DFD LEVELS BALANCE. 23 to 26. Level 0 must show the same external
     entities as Level 1 with the same flow directions across the boundary, and
     each Level 2 must show exactly the flows its parent process has on Level 1.

Nothing here renders anything, so it runs anywhere Python does.
"""
import glob
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))


def plain(v):
    """Readable text from a draw.io value: UNESCAPE first, then strip markup."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(v or ""))).strip()


def pages(path):
    root = ET.fromstring(open(path, encoding="utf-8").read())
    out = []
    for d in root.iter("diagram"):
        nodes, edges = {}, []
        for c in d.iter("mxCell"):
            st = c.get("style") or ""
            if c.get("vertex") == "1":
                nodes[c.get("id")] = (plain(c.get("value")), st)
            elif c.get("edge") == "1":
                edges.append((c.get("source"), c.get("target"),
                              plain(c.get("value"))))
        out.append((d.get("name") or os.path.basename(path), nodes, edges))
    return out


def one(path):
    p = pages(path)
    if len(p) != 1:
        raise SystemExit("%s has %d pages, expected 1" % (path, len(p)))
    return p[0]


def find(prefix):
    hits = sorted(glob.glob(os.path.join(HERE, prefix + "*.drawio")))
    if not hits:
        raise SystemExit("no file matching %s*.drawio" % prefix)
    return hits[0]


def internal(name):
    return name.startswith(":") or "[*]" in name or re.match(r"\w+\s*:\s*\w", name)


# ---------------------------------------------------------------- 1 and 2 ---
def check_sequence(bad):
    ssd = one(find("11_"))
    uc = one(find("01_"))
    _n, uc_nodes, _e = uc
    uc_ids = {re.match(r"(UC-\d\d)", v).group(1)
              for v, st in uc_nodes.values()
              if st.startswith("ellipse") and re.match(r"(UC-\d\d)", v)}
    uc_actors = {v for v, st in uc_nodes.values() if "umlActor" in st and v}

    _name, nodes, edges = ssd
    lifelines = {k: v for k, (v, st) in nodes.items() if "umlLifeline" in st}
    system = {k: v for k, v in lifelines.items() if v.startswith(":")}
    actors = {k: v for k, v in lifelines.items() if not v.startswith(":")}
    print("  SSD: %d actor lifeline(s), %d system, %d messages"
          % (len(actors), len(system), len(edges)))
    if len(system) != 1:
        bad.append("SSD has %d system lifelines; an SSD has exactly one"
                   % len(system))
    sysid = next(iter(system), None)
    cited = set()
    for s, t, label in edges:
        if sysid and sysid not in (s, t):
            bad.append("SSD message %r never touches the system lifeline, so it "
                       "is not a black box view" % label[:46])
        m = re.search(r"\[(UC-\d\d)\]", label)
        if m:
            cited.add(m.group(1))
            if m.group(1) not in uc_ids:
                bad.append("SSD cites %s, which is not in the use case diagram"
                           % m.group(1))
    if not cited:
        bad.append("no SSD message cites a use case, so that check is vacuous")
    for a in actors.values():
        if a not in uc_actors:
            bad.append("SSD actor %r is not on the use case diagram %s"
                       % (a, sorted(uc_actors)))
    print("  SSD covers %d of %d use cases" % (len(cited & uc_ids), len(uc_ids)))

    for n in range(12, 19):
        path = find("%02d_" % n)
        names = [v for v, st in one(path)[1].values() if "umlLifeline" in st and v]
        if not any(internal(v) for v in names):
            bad.append("%s shows no internal lifeline, so it is a black box view "
                       "and belongs with the SSD, not in behaviour design"
                       % os.path.basename(path))
    print("  design sequence diagrams 12-18: all show internal lifelines")


# -------------------------------------------------------------------- 3 -----
def boundary(nodes, edges):
    cross = {}
    for s, t, _l in edges:
        sv, tv = nodes.get(s), nodes.get(t)
        if not sv or not tv:
            continue
        if sv[1].startswith("shape=rect") and not tv[1].startswith("shape=rect"):
            cross.setdefault(sv[0], set()).add("in")
        elif tv[1].startswith("shape=rect") and not sv[1].startswith("shape=rect"):
            cross.setdefault(tv[0], set()).add("out")
    return cross


def touching(nodes, edges, prefix):
    pid = next((k for k, (v, st) in nodes.items()
                if st.startswith("rounded=1") and v.startswith(prefix)), None)
    if pid is None:
        return None
    out = set()
    for s, t, label in edges:
        if t == pid:
            out.add(("in", label))
        elif s == pid:
            out.add(("out", label))
    return out


def check_dfd(bad):
    l0 = one(find("23_"))
    l1 = one(find("24_"))
    b0, b1 = boundary(l0[1], l0[2]), boundary(l1[1], l1[2])
    print("  DFD entities: L0 %s | L1 %s" % (sorted(b0), sorted(b1)))
    for e in set(b0) ^ set(b1):
        bad.append("DFD entity %r is on one level but not the other" % e)
    for e in set(b0) & set(b1):
        if b0[e] != b1[e]:
            bad.append("DFD entity %r flows %s at Level 0 but %s at Level 1"
                       % (e, sorted(b0[e]), sorted(b1[e])))
    n_proc = sum(1 for _v, st in l0[1].values() if st.startswith("rounded=1"))
    if n_proc != 1:
        bad.append("DFD Level 0 has %d processes; a context diagram has one"
                   % n_proc)

    for num, prefix in (("25_", "2."), ("26_", "3.")):
        child = one(find(num))
        parent = "P" + prefix[0]
        up = touching(l1[1], l1[2], parent)
        if up is None:
            bad.append("DFD: %s is not a process on Level 1" % parent)
            continue
        down = set()
        for s, t, label in child[2]:
            sv, tv = child[1].get(s), child[1].get(t)
            if not sv or not tv:
                continue
            if sv[1].startswith("shape=rect") and not tv[1].startswith("shape=rect"):
                down.add(("in", label))
            elif tv[1].startswith("shape=rect") and not sv[1].startswith("shape=rect"):
                down.add(("out", label))
        print("  DFD %s: Level 1 has %d boundary flows, Level 2 has %d"
              % (parent, len(up), len(down)))
        for f in sorted(up - down):
            bad.append("DFD %s: Level 1 flow (%s) %r missing from Level 2"
                       % (parent, f[0], f[1]))
        for f in sorted(down - up):
            bad.append("DFD %s: Level 2 flow (%s) %r is not on Level 1"
                       % (parent, f[0], f[1]))


def main():
    bad = []
    check_sequence(bad)
    check_dfd(bad)
    if bad:
        print("\nFAIL (%d):" % len(bad))
        for b in bad:
            print("   ! " + b)
        return 1
    print("\nok: the SSD is a black box, 12-18 are design level, the DFD levels "
          "balance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
