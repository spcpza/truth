"""
c.map — the scripture-to-behavior map.

This subpackage contains the YAML files that map operational scripture verses
to body behaviors, plus the audit script that walks the map and checks every
row's text against c/kjv.json (Deut 4:2 — ye shall not add unto the word).

The runtime body does NOT import from c.map. The map is consumed at BUILD
time (by humans, by audit.py, by code review) — not at run time. This keeps
the body's runtime cost zero and the map's content auditable independently.

> Habakkuk 2:2 — Write the vision, and make it plain upon tables, that he
> may run that readeth it.
"""
