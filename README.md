# CityGen: real-world location to 3D city

Give it a latitude and longitude and it returns the surrounding city as clean
3D geometry: OpenStreetMap building footprints extruded into watertight
solids and seated on Copernicus GLO-30 terrain, in metres, with true north
along +Y.

Part of [Atlas](https://github.com/ssnfts/atlas). Extracted as a standalone
tool; nothing here imports anything outside this folder.

## What it does

- **Fetches building footprints** for any site from OpenStreetMap through
  the Overpass API, including courtyards and multi-part outlines.
- **Resolves a height for every building** from its tags and records where
  that height came from.
- **Extrudes watertight solids.** Triangulation is ear-clipping with an area
  check, so a polygon that lost a piece fails loudly instead of rendering
  short. Badly mapped footprints are returned in a `skipped` list with the
  reason.
- **Fetches terrain** from Copernicus DEM GLO-30 (30 m) using HTTP range
  requests, so a 1 km site downloads kilobytes, not a 22 MB tile.
- **Seats each building on the ground** using the lowest point under its
  footprint, so nothing floats on a slope.
- **Writes an attribution manifest** with the notices the data licences
  require.
- **Sends the result to 3ds Max** through the included bridge client, with
  sun, sky and camera helpers for V-Ray.

## Prerequisites

- Python 3.11 or later.
- An internet connection for the map and terrain downloads.
- Optional: `rasterio` and `numpy` for terrain.
- Optional: `tzdata` and `timezonefinder` for local time to sun position.
- Optional: 3ds Max with V-Ray, plus the in-Max half of the
  [3ds Max Python bridge](https://github.com/ssnfts/3dsMax-Python-bridge),
  to build the scene in 3ds Max. The geometry itself needs no 3D software.

## Install

```
git clone https://github.com/ssnfts/CityGen.git
cd CityGen
python -m pip install rasterio numpy tzdata timezonefinder
python -m pip install pytest shapely
```

Both `pip` lines are optional: the first adds terrain and time zones, the
second is for the tests. Footprints and extrusion use only the standard
library.

## How to use it

```python
import sys
sys.path.insert(0, "server")

from frame import SceneFrame
import osm, massing, terrain

# 1. The site. Everything is measured in metres from this point.
frame = SceneFrame(origin_lat=25.0805, origin_lon=55.1403)

# 2. Buildings within 500 m.
buildings = osm.fetch_for_site(frame, radius_m=500)

# 3. Terrain within 1.5 km (optional, needs rasterio).
patch = terrain.fetch_for_site(frame, radius_m=1500)
ground_mesh = patch.to_mesh(frame)

# 4. Solids, seated on the terrain.
meshes, skipped = massing.buildings_to_meshes(
    buildings, frame, ground=patch.elevation_at
)
print(len(meshes), "buildings,", len(skipped), "skipped")
```

Each `Mesh` has `verts` (metres), `faces` (0-based triangles) and `name`.
Write them to OBJ, or send them straight to 3ds Max:

```python
from maxbridge import MaxBridge

bridge = MaxBridge()        # start the bridge inside 3ds Max first
bridge.create_meshes([(m.name, m.verts, m.faces) for m in meshes])
```

Use `attribution.manifest_for_build(...)` to produce the credits for the
data you used.

## Getting the best result

- **Check `skipped`.** If a large share of a district was skipped, the area
  is poorly mapped; widen the radius or pick another centre.
- **Check `height_source`.** Many buildings have no height in OpenStreetMap
  and get an 8 m default. For a hero skyline, correct the important towers
  by hand.
- **Use more terrain than buildings.** A terrain radius two to three times
  the building radius gives a believable horizon.
- **Treat 30 m terrain as context.** It gives the silhouette and slope, not
  kerbs and steps. Model the foreground.
- **Run `terrain.looks_like_surface_model`** in dense cities. It tests
  whether the elevation data already has building heights baked in.
- **Keep the scene in metres with the site at the origin.** Large map
  coordinates cause viewport jitter and z-fighting.
- **Be gentle with the public Overpass server.** Cache what you fetch and
  avoid repeated large queries.

## Works well with

**Graphic design.** Render the massing white with a low sun for map
posters, location diagrams and pitch decks, or export an ambient-occlusion
pass and colour it in Photoshop, Affinity or Illustrator.

**Product visualization.** A real, recognisable backdrop for cars and
architecture. Add
[V-Ray material graph builder](https://github.com/ssnfts/V-Ray-material-graph-builder)
for facades and roads, and [Atlas](https://github.com/ssnfts/atlas) for the
correct sun for the date and time.

**Film and previs.** Location blocking before a shoot: where shadows fall,
which buildings block the sky, what the camera sees from a given position.
Add
[Cinematic camera moves](https://github.com/ssnfts/Cinematic-camera-moves)
for the shots. The meshes are plain triangles, so they can be exported to
Blender, Houdini or Unreal Engine as well.

**Automation.** Call it from a script or a scheduled job to build many
sites from a list of coordinates, or let an agent do it through
[3dsmax-mcp](https://github.com/ssnfts/3dsmax-mcp).

## Layout

```
server/   the modules
tests/    offline tests
```

## Tests

```
python -m pytest tests -q
```

6 test files. They are offline and need no 3ds Max and no network.

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
