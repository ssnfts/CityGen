# Real-world location to 3D city

Fetches OpenStreetMap footprints for any location, extrudes them into watertight solids, and seats them on Copernicus GLO-30 terrain. Ear-clipped triangulation with an area check, so a polygon that lost a piece fails instead of rendering short.

Part of Atlas. Extracted as a standalone tool; nothing here imports anything
outside this folder.

## Layout

```
server/   the modules
tests/    run these first
```

## Run the tests

```
python -m pytest tests -q
```

6 test files ship with this product.

Some need extra packages: `pip install shapely`.

## Requirements

Python 3.11+. The tests are offline and need no 3ds Max, no Houdini and no
network.

## Data licensing

This is source code, licensed however you choose. The *data* it fetches is
not:

- OpenStreetMap is ODbL 1.0 -- attribution, and share-alike on derived
  databases.
- Copernicus GLO-30 requires attribution.
- Poly Haven textures are CC0.

`attribution.py`, where included, generates the manifest for you.

## Compatibility

Every 3ds Max and V-Ray parameter name in this code was read off a live
3ds Max 2027 with V-Ray 7 update 3. Names are discovered from the host rather
than recalled, but they were discovered on *that* host. Treat other versions
as unverified until checked.
