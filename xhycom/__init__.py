"""xhycom — xarray interface for HYCOM a.b binary output files.

Public API
----------
open_dataset(path, ...)       Open a single archive snapshot.
open_mfdataset(paths, ...)    Open a time series of archive snapshots.
open_grid(basename, ...)      Open a regional.grid file.
open_bathy(basename, ...)     Open a bathymetry file.
"""
import warnings

import numpy as np
import xarray as xr

from ._abfile import ABFile, ABFileBathy, ABFileGrid, grid_ordered_fieldnames
from ._discovery import find_archv_files
from ._reader import read_one_archv

__version__ = "0.1.0"
__all__ = ["open_dataset", "open_mfdataset", "open_grid", "open_bathy"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_grid(grid, endian):
    """Accept a path string or a pre-loaded Dataset; return a Dataset."""
    if grid is None:
        return None
    if isinstance(grid, xr.Dataset):
        return grid
    return open_grid(grid, endian=endian)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def open_dataset(path, grid=None, endian="big"):
    """Open a single HYCOM archive ``.ab`` file pair as an ``xr.Dataset``.

    Parameters
    ----------
    path : str
        Path to the archive file.  The ``.a`` / ``.b`` extension is optional.
    grid : str or xr.Dataset, optional
        Path to ``regional.grid`` (without extension), or a Dataset already
        returned by :func:`open_grid`.  When provided, ``lon`` and ``lat``
        are attached as non-dimension coordinates on every variable.
    endian : str
        Byte order: ``"big"`` (default), ``"little"``, or ``"native"``.

    Returns
    -------
    xr.Dataset
        Dataset with:

        * A ``time`` dimension of size 1.  Use ``.isel(time=0)`` to drop it.
        * 2-D fields on ``(time, y, x)``.
        * Layered fields on ``(time, k, y, x)`` with ``k`` (layer index,
          1-based) and ``dens`` (target sigma-2 density) coordinates.
        * ``lon`` / ``lat`` 2-D curvilinear coordinates when *grid* is given.
        * Global attributes ``iversn``, ``iexpt``, ``yrflag``.

    Examples
    --------
    Open a snapshot without grid coordinates:

    >>> import xhycom
    >>> ds = xhycom.open_dataset("archv.2020_001_00")

    Open with grid coordinates attached:

    >>> ds = xhycom.open_dataset("archv.2020_001_00", grid="regional.grid")

    Select and plot surface temperature:

    >>> ds["temp"].isel(time=0, k=0).plot(x="lon", y="lat")
    """
    basename = ABFile.strip_ab_ending(str(path))
    grid_ds = _load_grid(grid, endian)
    return read_one_archv(basename, grid_ds=grid_ds, endian=endian)


def open_mfdataset(paths, grid=None, endian="big", skip_errors=False):
    """Open multiple HYCOM archive ``.ab`` file pairs as a single ``xr.Dataset``.

    Snapshots are concatenated along a ``time`` dimension in chronological
    order.

    Parameters
    ----------
    paths : str or list of str
        One of:

        * A directory path — all ``archv.YYYY_DDD_HH.[ab]`` pairs found
          inside are used.
        * A glob pattern such as ``"data/archv.2020_*.a"``.
        * An explicit list of archive basenames or filenames.

    grid : str or xr.Dataset, optional
        Grid file path or pre-loaded Dataset.  Loaded once and shared across
        all files for efficiency.
    endian : str
        Byte order.
    skip_errors : bool
        If ``True``, files that fail to open are skipped with a warning
        rather than raising an exception.  Default ``False``.

    Returns
    -------
    xr.Dataset
        Combined Dataset with a ``time`` dimension spanning all snapshots.

    Raises
    ------
    ValueError
        If *paths* is a string and no matching files are found.
    RuntimeError
        If all files fail to open when *skip_errors* is ``True``.

    Examples
    --------
    Open a whole year of 6-hourly output from a directory:

    >>> ds = xhycom.open_mfdataset("data/", grid="regional.grid")

    Open a subset using a glob:

    >>> ds = xhycom.open_mfdataset("data/archv.2020_0[0-3]*.a",
    ...                            grid="regional.grid")

    Compute and plot the time-mean surface salinity:

    >>> ds["saln"].isel(k=0).mean("time").plot(x="lon", y="lat")
    """
    if isinstance(paths, str):
        basenames = find_archv_files(paths)
    else:
        basenames = [ABFile.strip_ab_ending(str(p)) for p in paths]

    grid_ds = _load_grid(grid, endian)

    datasets = []
    for basename in basenames:
        try:
            datasets.append(read_one_archv(basename, grid_ds=grid_ds, endian=endian))
        except Exception as exc:
            if skip_errors:
                warnings.warn(f"Skipping {basename!r}: {exc}", stacklevel=2)
            else:
                raise

    if not datasets:
        raise RuntimeError("No files were successfully opened.")

    return xr.concat(datasets, dim="time", data_vars="minimal", compat="override")


def open_grid(basename="regional.grid", endian="big"):
    """Open a HYCOM ``regional.grid`` ``.ab`` file pair as an ``xr.Dataset``.

    Parameters
    ----------
    basename : str
        Path to the grid file without the ``.a`` / ``.b`` extension.
        Defaults to ``"regional.grid"`` in the current directory.
    endian : str
        Byte order.

    Returns
    -------
    xr.Dataset
        Dataset with all 19 grid variables on dims ``(y, x)``:
        ``plon``, ``plat``, ``ulon``, ``ulat``, ``vlon``, ``vlat``,
        ``qlon``, ``qlat``, ``pang``, ``scpx``, ``scpy``, ``scqx``,
        ``scqy``, ``scux``, ``scuy``, ``scvx``, ``scvy``, ``cori``, ``pasp``.

    Notes
    -----
    The HYCOM grid is curvilinear; all coordinate arrays are 2-D.
    Use ``grid["plon"]`` and ``grid["plat"]`` for tracer (p-point) positions.

    Examples
    --------
    >>> grid = xhycom.open_grid("regional.grid")
    >>> grid["plon"].shape
    (800, 880)
    """
    basename = ABFile.strip_ab_ending(str(basename))
    gf = ABFileGrid(basename, "r", endian=endian)
    data_vars = {}
    for fname in grid_ordered_fieldnames:
        raw = gf.read_field(fname)
        if raw is not None:
            data_vars[fname] = xr.DataArray(
                np.ma.filled(raw.astype(np.float64), np.nan),
                dims=["y", "x"],
                name=fname,
            )
    gf.close()
    return xr.Dataset(data_vars)


def open_bathy(basename, idm=None, jdm=None, grid=None, endian="big"):
    """Open a HYCOM bathymetry ``.ab`` file pair as an ``xr.Dataset``.

    Grid dimensions (*idm*, *jdm*) are required by the HYCOM binary format
    but are not stored in the bathymetry file itself.  Supply them directly
    or let xhycom infer them from a *grid* file.

    Parameters
    ----------
    basename : str
        Path to the bathymetry file without the ``.a`` / ``.b`` extension.
    idm : int, optional
        Number of grid points in the x-direction.
    jdm : int, optional
        Number of grid points in the y-direction.
    grid : str or xr.Dataset, optional
        Path to ``regional.grid`` or a pre-loaded grid Dataset.  Used to
        infer *idm* / *jdm* and to attach ``lon`` / ``lat`` coordinates.
    endian : str
        Byte order.

    Returns
    -------
    xr.Dataset
        Dataset with a ``depth`` variable (metres) on dims ``(y, x)``.
        ``lon`` / ``lat`` coordinates are attached when *grid* is provided.

    Raises
    ------
    ValueError
        If neither (*idm*, *jdm*) nor *grid* are supplied.

    Examples
    --------
    >>> bathy = xhycom.open_bathy("depth_TP2a0.10_04", grid="regional.grid")
    >>> bathy["depth"].plot(x="lon", y="lat")
    """
    basename = ABFile.strip_ab_ending(str(basename))
    grid_ds = _load_grid(grid, endian)

    if idm is None or jdm is None:
        if grid_ds is None:
            raise ValueError(
                "Either (idm, jdm) or grid must be supplied to open_bathy."
            )
        jdm_inferred, idm_inferred = grid_ds["plon"].shape
        idm = idm if idm is not None else idm_inferred
        jdm = jdm if jdm is not None else jdm_inferred

    bf = ABFileBathy(basename, "r", idm=idm, jdm=jdm, endian=endian)
    raw = bf.read_field("depth")
    bf.close()

    coords = {}
    if grid_ds is not None:
        coords["lon"] = (["y", "x"], grid_ds["plon"].values)
        coords["lat"] = (["y", "x"], grid_ds["plat"].values)

    da = xr.DataArray(
        np.ma.filled(raw.astype(np.float64), np.nan),
        dims=["y", "x"],
        coords=coords,
        attrs={"units": "m", "long_name": "sea floor depth"},
        name="depth",
    )
    return xr.Dataset({"depth": da})
