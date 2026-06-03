# How it works

## The HYCOM `.a/.b` binary format

HYCOM writes model output as pairs of binary files:

| File | Content |
|------|---------|
| `archv.YYYY_DDD_HH.b` | Plain-text header with field names, levels, min/max |
| `archv.YYYY_DDD_HH.a` | Big-endian IEEE 754 single-precision binary data |

xhycom reads the `.b` header to discover field names and layout, then memory-maps the `.a` file to extract each field as a NumPy array.

## Dataset structure

The returned `xr.Dataset` reflects HYCOM's staggered Arakawa C-grid.

### Horizontal dimensions and coordinates

All variables share the same `y`, `x` array dimensions (size `jdm × idm`), but carry grid-point-appropriate lon/lat coordinates:

| Staggering | Variables | Coordinates |
|-----------|-----------|-------------|
| T-point (cell centre) | `temp`, `salin`, `thknss`, `density`, … | `lon`, `lat` (from `plon`, `plat`) |
| U-point (cell face in x) | `u-vel.`, `u_btrop`, `umix` | `lon_u`, `lat_u` (from `ulon`, `ulat`) |
| V-point (cell face in y) | `v-vel.`, `v_btrop`, `vmix` | `lon_v`, `lat_v` (from `vlon`, `vlat`) |

### Vertical dimensions and coordinates

| Dimension | Levels | Variables |
|-----------|--------|-----------|
| `k` | 1 … N (layer centres) | `temp`, `salin`, `u-vel.`, `v-vel.`, `thknss`, … |
| `ki` | 0 … N (layer interfaces) | interface pressures and similar diagnostics |
| *(none)* | single level | 2-D surface diagnostics (`srfhgt`, `montg1`, …) |

- **`dens` coordinate** — target sigma density for each layer centre, attached to the `k` dimension. Taken from T-point variables (`thknss` preferred) because the layer density is defined at the tracer point; U/V-point values are spatial averages of neighbouring cells.
- **`time` coordinate** — absolute calendar date decoded from the HYCOM model day using `yrflag` and [`cftime`](https://unidata.github.io/cftime).

## Time coordinate and yrflag

HYCOM stores time as a floating-point "model day" whose meaning depends on the `yrflag` parameter in `blkdat.input`:

| yrflag | Calendar | Epoch |
|--------|----------|-------|
| 0 | 360-day | Jan 16, year 1 |
| 1 | 366-day | Jan 16, year 1 |
| 2 | 366-day | Jan  1, year 1 |
| 3 | Gregorian | Jan 1, 1901 |
| 4 | 365-day | Jan  1, year 1 |
| 5 | 365-day | Jan  1, 1901 |

`yrflag=3` (Gregorian) is the most common setting for real HYCOM runs.  xhycom reads `yrflag` directly from the `.b` header, so no manual configuration is needed.

## Curvilinear coordinates and plotting

Because `lon` and `lat` are 2-D, pass them explicitly to plotting functions:

```python
# xarray built-in plot
ds["temp"].isel(time=0, k=0).plot(x="lon", y="lat")
```
