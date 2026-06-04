# Why xarray?

xhycom returns [xarray](https://docs.xarray.dev) Datasets.  If you have not
used xarray before, this page explains why that is a good thing.

---

## From raw indices to labelled dimensions

A NumPy array is a grid of numbers.  The only way to refer to a location is
by its integer position:

```python
arr[0, 5, 100, 200]   # what does this mean?
```

An **xarray DataArray** wraps the same numbers but gives every axis a name and
every point along that axis a coordinate value:

```
NumPy array (shape only)          xarray DataArray (shape + meaning)
──────────────────────────────    ──────────────────────────────────────────
arr.shape                         da.dims
(120, 40, 880, 800)               ('time', 'k', 'y', 'x')

arr[0, 5, :, :]                   da.isel(time=0, k=5)       # by index
                                  da.sel(time='1993-01-15')  # by label

no coordinates                    Coordinates:
no labels                           time  (time)  cftime 1993-01-15 …
no units                            k     (k)     int64  1 2 … 40
                                    dens  (k)     float64 1026.5 …
                                    lon   (y, x)  float64 …
                                    lat   (y, x)  float64 …
                                  Attributes:
                                    units: degC
                                    long_name: sea water potential temperature
```

You select by *what* rather than *where*, and the code reads like the science.

---

## Coordinates travel with the data

Operations on an xarray object preserve coordinates automatically.  Slice a
region, take a time mean, compute an anomaly — the result always knows where
it is:

```
ds["temp"]                        ds["temp"].isel(k=0).mean("time")
──────────────────────────────    ──────────────────────────────────
dims: (time, k, y, x)             dims: (y, x)
coords:                           coords:
  time  1993-01 … 2022-12           lon  (y, x)  float64 …
  k     1 … 40                      lat  (y, x)  float64 …
  dens  1026.5 …                 attrs: units: degC
  lon   (y, x)
  lat   (y, x)
```

With raw NumPy you would have to carry `lon`, `lat`, and the time axis
bookkeeping yourself and reattach them after every operation.

---

## Plotting just works

Because coordinates are embedded in the data, xarray's `.plot()` method
automatically labels axes, titles, and colourbars:

```python
ds["temp"].isel(time=0, k=0).plot(x="lon", y="lat")
```

With NumPy + Matplotlib you would need to pass `plon` and `plat` explicitly,
set axis labels by hand, and add the colourbar yourself.

---

## Larger-than-memory data via Dask

xarray integrates with [Dask](https://docs.dask.org) to represent datasets
that are far larger than available RAM.  Instead of reading data immediately,
xarray builds a *computation graph*: a recipe for what to do when you finally
ask for the result.

```
                          open_mfdataset(..., chunks={"time": 1})
                          ┌─────────────────────────────────────┐
30 years of .ab files ───►│  Dask-backed xr.Dataset             │
(~1 TB on disk)           │  in memory: ~100 MB (graph only)    │
                          └───────────────┬─────────────────────┘
                                          │  .isel(k=0).mean("time")
                                          ▼
                          ┌─────────────────────────────────────┐
                          │  lazy computation graph             │
                          │  (still nothing read from disk)     │
                          └───────────────┬─────────────────────┘
                                          │  .compute()
                                          ▼
                          ┌─────────────────────────────────────┐
                          │  result: (y, x) NumPy array         │
                          │  only the needed chunks were read   │
                          └─────────────────────────────────────┘
```

This is what makes it possible to compute a 30-year mean SST on a laptop
without running out of memory.

---

## The broader ecosystem

An xarray Dataset plugs into a large ecosystem of scientific Python tools
without any glue code:

| Task | Tool |
|---|---|
| Interactive maps | [hvPlot](https://hvplot.holoviz.org) / [GeoViews](https://geoviews.org) |
| Parallel computation | [Dask](https://docs.dask.org) |
| Cloud-optimised storage | [Zarr](https://zarr.dev) |
| Regridding | [xESMF](https://xesmf.readthedocs.io) |
| Statistics | [xskillscore](https://xskillscore.readthedocs.io), [climpred](https://climpred.readthedocs.io) |
| Filtering | [xrft](https://xrft.readthedocs.io), [scipy](https://docs.scipy.org) |

Because xhycom returns standard xarray objects, all of these work on HYCOM
output immediately — no adapters or format conversions required.
