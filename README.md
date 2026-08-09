# CityGen for 3ds Max 2027

CityGen is a native, drag-and-drop 3ds Max 2027 tool. Select any closed planar
mesh or spline, open CityGen from the Command Panel, then generate a fully
detached, versioned city inside that exact boundary.

It has no AI, MCP, TCP bridge, V-Ray, Houdini, Blender, or external DCC runtime
dependency. Real-world generation uses ordinary HTTPS data requests; procedural
generation works entirely from the selected boundary and seed.

## Layout

```
server/       dependency-free geometry, data, hydrology, and transport core
max_package/  drag-and-drop MZP source package for 3ds Max 2027
tests/        offline core and package contracts
```

## Run the tests

```
"C:\\Program Files\\Autodesk\\3ds Max 2027\\Python\\python.exe" -m pytest tests -q --basetemp=.pytest-tmp
```

The optional geometry cross-validation tests need `shapely`.

## Requirements

3ds Max 2027 on Windows. The dependency-free core tests are offline; the native
package is verified in 3ds Max as part of release acceptance.

## Install in 3ds Max

Zip the contents of `max_package/` as `CityGen.mzp`, then drag it into 3ds Max.
The installer copies its scripts to the user scripts directory and registers
the **CityGen** macro. Add that macro to a toolbar through Customize User
Interface.

The map picker opens in the default browser and returns the selected site to
CityGen. It is a short-lived browser callback, not a persistent local bridge.

## Generation contract

- **Procedural mode** creates road, block, building, water, terrain, bridge, and
  prop categories from the boundary and deterministic seed.
- **Real-world mode** preserves mapped OSM features and fills sparse areas with
  explicitly marked procedural infill.
- **Draft**, **Production**, and **Hero** tiers expose predictable budgets.
- Every run creates a new `CG_<site>_v###` layer set; it never overwrites a
  prior result or user edits.
- Bridges and tunnels with missing vertical data are reconstructed from terrain
  and transport tags, then included in the `Review_InferredTransport` set.

## Data licensing

This is source code, licensed however you choose. The data it fetches is not:

- OpenStreetMap is ODbL 1.0 -- attribution, and share-alike on derived
  databases.
- Copernicus GLO-30 requires attribution.
- JRC Global Surface Water and GEBCO need their respective attributions.
- Bundled assets must be redistributable; user asset libraries remain theirs.

`attribution.py`, where included, generates the manifest for you.

## Compatibility

Only 3ds Max 2027 is supported.
