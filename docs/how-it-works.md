# How it works

## The HYCOM `.a/.b` binary format

HYCOM writes model output as pairs of binary files:

| File | Content |
|------|---------|
| `archv.YYYY_DDD_HH.b` | Plain-text header with field names, levels, min/max |
| `archv.YYYY_DDD_HH.a` | Big-endian IEEE 754 single-precision binary data |

xhycom reads the `.b` header to discover field names and layout, then memory-maps the `.a` file to extract each field as a NumPy array.

## Dataset structure

The returned `xr.Dataset` is assembled with:

- **`y`, `x` dimensions** — grid index dimensions (j and i).
- **`lon`, `lat` coordinates** — 2-D curvilinear coordinates from `regional.grid.ab`, attached as non-dimension coordinates.  Because HYCOM uses a curvilinear grid, these are always 2-D arrays.
- **`k` coordinate** — HYCOM layer index (1-based), on layered variables.
- **`dens` coordinate** — target sigma-2 density for each hybrid layer, on layered variables.
- **`time` coordinate** — absolute calendar date converted from the HYCOM model day using `yrflag` and [`cftime`](https://unidata.github.io/cftime).

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
