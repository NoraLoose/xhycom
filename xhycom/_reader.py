"""Core reader: one HYCOM archive .ab pair → xr.Dataset."""
from collections import defaultdict

import numpy as np
import xarray as xr

from ._abfile import ABFileArchv
from ._time import model_day_to_datetime


def _fill(arr):
    """Masked array → float64 ndarray, masked values replaced by NaN."""
    return np.ma.filled(arr.astype(np.float64), np.nan)


def read_one_archv(basename, grid_ds=None, endian="big"):
    """Read a single HYCOM archive ``.ab`` file pair into an ``xr.Dataset``.

    Fields with multiple vertical layers become ``(time, k, y, x)``
    DataArrays.  Single-level fields (e.g. ``srfhgt``, ``montg1``) become
    ``(time, y, x)``.  The ``time`` dimension always has size 1 so that
    multiple snapshots can be combined with ``xr.concat``.

    Parameters
    ----------
    basename : str
        Path to the archive file without the ``.a`` / ``.b`` extension.
    grid_ds : xr.Dataset, optional
        Dataset returned by :func:`xhycom.open_grid`.  When supplied, ``lon``
        and ``lat`` (from the p-grid) are attached as 2-D non-dimension
        coordinates on every variable.
    endian : str
        Byte order: ``"big"`` (default), ``"little"``, or ``"native"``.

    Returns
    -------
    xr.Dataset
        Dataset with:

        * ``time`` dimension of size 1
        * ``(time, y, x)`` for 2-D fields
        * ``(time, k, y, x)`` for layered fields, with ``k`` (layer index,
          1-based) and ``dens`` (target sigma-2 density) as coordinates
        * ``lon`` / ``lat`` 2-D curvilinear coordinates if *grid_ds* is given
        * Global attributes ``iversn``, ``iexpt``, ``yrflag``
    """
    af = ABFileArchv(basename, "r", endian=endian)

    # Build fieldname → {k: dens} (dict key deduplicates repeated records)
    field_kdens = defaultdict(dict)
    for rec in af.fields.values():
        field_kdens[rec["field"]][rec["k"]] = rec["dens"]

    yrflag = af.yrflag
    first_rec = next(iter(af.fields.values())) if af.fields else {}
    model_day = first_rec.get("day")

    global_attrs = {"iversn": af.iversn, "iexpt": af.iexpt, "yrflag": yrflag}

    base_coords = {}
    if grid_ds is not None:
        base_coords["lon"] = (["y", "x"], grid_ds["plon"].values)
        base_coords["lat"] = (["y", "x"], grid_ds["plat"].values)

    data_vars = {}
    for fname, kdens in field_kdens.items():
        levels = sorted(kdens)

        if len(levels) == 1:
            raw = af.read_field(fname, levels[0])
            data_vars[fname] = xr.DataArray(
                _fill(raw), dims=["y", "x"],
                coords=dict(base_coords), name=fname,
            )
        else:
            stack = np.stack([_fill(af.read_field(fname, k)) for k in levels])
            coords = dict(base_coords)
            coords["k"] = ("k", levels)
            coords["dens"] = ("k", [kdens[k] for k in levels])
            data_vars[fname] = xr.DataArray(
                stack, dims=["k", "y", "x"],
                coords=coords, name=fname,
            )

    af.close()

    ds = xr.Dataset(data_vars, attrs=global_attrs)

    if model_day is not None and yrflag is not None:
        t = model_day_to_datetime(model_day, yrflag)
        ds = ds.expand_dims({"time": [t]})

    return ds
