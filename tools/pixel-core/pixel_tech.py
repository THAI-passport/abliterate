#!/usr/bin/env python3
"""PixelTech: the rig, refine, cleanup, tileset and nine-slice tools.

Deterministic, dependency-light companions to ``pixel_tool.py``. They never
generate art with a model: every pixel comes from a hand-authored text grid or
from a rule applied to one. The formats and workflows are documented in
``docs/PixelTech.md`` and in the ``pixel-rig``, ``pixel-refine``,
``pixel-cleanup``, ``pixel-tileset`` and ``pixel-nineslice`` skills.

Grids are handled as lists of rows of palette colour names (``None`` is
transparent), so every operation stays on the locked palette.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pixel_core import (  # noqa: E402
    Palette,
    PixelCoreError,
    _GRID_SYMBOLS,
    _nearest_color,
    load_palette,
    parse_grid_text,
    require_pillow,
)

try:  # Pillow is required for image output only.
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

NameGrid = list[list[str | None]]
TRANSPARENT = {"transparent", "none", "alpha"}


class PixelTechError(PixelCoreError):
    """A user-facing error from the PixelTech tools."""


def _where(source: str | Path | None, line: int = 1) -> str:
    """Return a stable source location for all user-facing input errors."""

    return f"{Path(source) if source is not None else '<input>'}:{line}"


def _line_of(source: str | Path, token: str) -> int:
    """Best-effort line lookup for semantic errors in JSON and grid headers."""

    try:
        for number, line in enumerate(Path(source).read_text(encoding="utf-8").splitlines(), 1):
            if token in line:
                return number
    except OSError:
        pass
    return 1


def _line_of_nth(source: str | Path, token: str, occurrence: int) -> int:
    try:
        seen = 0
        for number, line in enumerate(Path(source).read_text(encoding="utf-8").splitlines(), 1):
            if token in line:
                seen += 1
                if seen == occurrence:
                    return number
    except OSError:
        pass
    return 1


def _fail(source: str | Path | None, message: str, *, line: int = 1) -> PixelTechError:
    return PixelTechError(f"{_where(source, line)}: {message}")


# ---------------------------------------------------------------------------
# Grids: read, write, convert
# ---------------------------------------------------------------------------


@dataclass
class Grid:
    """A text grid resolved to colour names, with its headers kept for rewriting."""

    width: int
    height: int
    frames: list[NameGrid]
    headers: dict[str, str] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)
    source: Path | None = None

    @property
    def pivot(self) -> tuple[int, int]:
        line = _line_of(self.source, "pivot:") if self.source else 1
        return _xy(self.headers.get("pivot", "0,0"), f"{_where(self.source, line)}: pivot")

    def anchor(self, name: str) -> tuple[int, int] | None:
        """Return a named point in part-local coordinates."""

        key = f"anchor-{name}"
        if key not in self.headers:
            return None
        line = _line_of(self.source, f"{key}:") if self.source else 1
        return _xy(self.headers[key], f"{_where(self.source, line)}: {key}")


def _xy(value: str | Sequence[int], label: str) -> tuple[int, int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
    else:
        parts = [str(part) for part in value]
    if len(parts) != 2:
        raise PixelTechError(f"{label} must be two integers, got {value!r}")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise PixelTechError(f"{label} must be two integers, got {value!r}") from exc


def read_grid(path: str | Path, palette: Palette | None = None) -> Grid:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise _fail(source, "grid not found") from exc
    asset = parse_grid_text(text, source=source)
    comments = []
    for line in text.splitlines():
        if line.startswith("#"):
            comments.append(line)
        elif line.strip():
            break
    frames: list[NameGrid] = []
    for frame in asset.frames:
        rows: NameGrid = []
        if len(frame) != asset.height:
            raise _fail(source, f"a frame has {len(frame)} rows, expected {asset.height}")
        for row in frame:
            if len(row) != asset.width:
                raise _fail(source, f"a row is {len(row)} wide, expected {asset.width}")
            names: list[str | None] = []
            for symbol in row:
                if symbol == "." and symbol not in asset.legend:
                    names.append(None)
                    continue
                name = asset.legend.get(symbol)
                if name is None:
                    raise _fail(source, f"symbol {symbol!r} is not in the legend")
                names.append(None if name.strip().lower() in TRANSPARENT else name)
            rows.append(names)
        frames.append(rows)
    headers = {"size": f"{asset.width}x{asset.height}", "palette": asset.palette_name}
    if asset.origin is not None:
        headers["origin"] = f"{asset.origin[0]},{asset.origin[1]}"
    headers.update(asset.metadata)
    grid = Grid(asset.width, asset.height, frames, headers, comments, source)
    if palette is not None:
        check_names(grid.frames, palette, _where(source))
    return grid


def check_names(frames: Iterable[NameGrid], palette: Palette, label: str) -> None:
    known = palette.by_name
    for frame in frames:
        for row in frame:
            for name in row:
                if name is not None and name not in known:
                    raise PixelTechError(f"{label}: colour {name!r} is not in palette {palette.name!r}")


def format_frames(
    frames: Sequence[NameGrid],
    palette: Palette,
    headers: Mapping[str, str],
    comments: Sequence[str] = (),
) -> str:
    """Write one or more frames as a text grid, with a legend in palette order."""

    if not frames or not frames[0] or not frames[0][0]:
        raise PixelTechError("cannot write an empty grid")
    height, width = len(frames[0]), len(frames[0][0])
    for frame in frames:
        if len(frame) != height or any(len(row) != width for row in frame):
            raise PixelTechError("all frames must share one size")
    check_names(frames, palette, "output")
    used = {name for frame in frames for row in frame for name in row if name}
    ordered = [color.name for color in palette.colors if color.name in used]
    if len(ordered) > len(_GRID_SYMBOLS):
        raise PixelTechError(f"{len(ordered)} colours exceed the {len(_GRID_SYMBOLS)} legend symbols")
    symbol = {name: _GRID_SYMBOLS[index] for index, name in enumerate(ordered)}
    head = dict(headers)
    head["size"] = f"{width}x{height}"
    head["palette"] = palette.name
    head["frames"] = str(len(frames))
    lines = list(comments)
    for key in ("size", "palette", "frames", "origin"):
        if key in head:
            lines.append(f"{key}: {head[key]}")
    for key, value in head.items():
        if key not in {"size", "palette", "frames", "origin"}:
            lines.append(f"{key}: {value}")
    lines += ["legend:", "  . = transparent"] + [f"  {symbol[n]} = {n}" for n in ordered]
    for index, frame in enumerate(frames):
        lines.append("grid:" if len(frames) == 1 else f"frame {index + 1}:")
        lines += ["".join("." if n is None else symbol[n] for n in row) for row in frame]
    return "\n".join(lines) + "\n"


def blank(width: int, height: int) -> NameGrid:
    if width <= 0 or height <= 0:
        raise PixelTechError(f"grid dimensions must be positive, got {width}x{height}")
    return [[None] * width for _ in range(height)]


def _dimensions(grid: NameGrid, label: str = "grid") -> tuple[int, int]:
    if not grid or not grid[0]:
        raise PixelTechError(f"{label} is empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise PixelTechError(f"{label} has uneven row widths")
    return width, len(grid)


def to_image(grid: NameGrid, palette: Palette) -> "Image.Image":
    require_pillow()
    width, height = _dimensions(grid)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    known = palette.by_name
    pixels = image.load()
    for y, row in enumerate(grid):
        for x, name in enumerate(row):
            if name is not None:
                pixels[x, y] = known[name].rgba
    return image


def from_image(image: "Image.Image", palette: Palette, *, nearest: bool = False) -> NameGrid:
    """Read an image back to colour names; exact matches only unless ``nearest``."""

    require_pillow()
    image = image.convert("RGBA")
    by_rgb = palette.first_by_rgb()
    grid: NameGrid = []
    for y in range(image.height):
        row: list[str | None] = []
        for x in range(image.width):
            r, g, b, a = image.getpixel((x, y))
            if a < 128:
                row.append(None)
            elif (r, g, b) in by_rgb:
                row.append(by_rgb[(r, g, b)].name)
            elif nearest:
                row.append(_nearest_color((r, g, b), palette).name)
            else:
                raise PixelTechError(f"pixel {x},{y} #{r:02x}{g:02x}{b:02x} is off-palette")
        grid.append(row)
    return grid


def flip_h(grid: NameGrid) -> NameGrid:
    return [list(reversed(row)) for row in grid]


def blit(canvas: NameGrid, sprite: NameGrid, x0: int, y0: int, clip: list[str] | None = None) -> None:
    width, height = _dimensions(canvas, "canvas")
    _dimensions(sprite, "sprite")
    for y, row in enumerate(sprite):
        for x, name in enumerate(row):
            if name is None:
                continue
            cx, cy = x0 + x, y0 + y
            if 0 <= cx < width and 0 <= cy < height:
                canvas[cy][cx] = name
            elif clip is not None:
                clip.append(f"{cx},{cy}")


def save_png(image: "Image.Image", path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)
    return output


def scaled(image: "Image.Image", scale: int) -> "Image.Image":
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def on_background(image: "Image.Image", color: tuple[int, int, int, int] = (40, 42, 54, 255)) -> "Image.Image":
    base = Image.new("RGBA", image.size, color)
    base.alpha_composite(image)
    return base


def sheet(images: Sequence["Image.Image"], columns: int, gap: int = 2, bg=(40, 42, 54, 255)) -> "Image.Image":
    if not images:
        raise PixelTechError("nothing to lay out")
    if columns <= 0:
        raise PixelTechError("sheet columns must be positive")
    cell_w = max(i.width for i in images)
    cell_h = max(i.height for i in images)
    rows = math.ceil(len(images) / columns)
    out = Image.new("RGBA", (gap + columns * (cell_w + gap), gap + rows * (cell_h + gap)), bg)
    for index, image in enumerate(images):
        col, row = index % columns, index // columns
        out.alpha_composite(image, (gap + col * (cell_w + gap), gap + row * (cell_h + gap)))
    return out


def one_and_four(image: "Image.Image", bg=(40, 42, 54, 255)) -> "Image.Image":
    """The review layout every tool emits: 1x beside 4x on the dark review background."""

    big = scaled(image, 4)
    out = Image.new("RGBA", (image.width + big.width + 12, max(image.height, big.height) + 8), bg)
    out.alpha_composite(image, (4, 4))
    out.alpha_composite(big, (image.width + 8, 4))
    return out


# ---------------------------------------------------------------------------
# Shared pixel operations (used by the rig and by refine)
# ---------------------------------------------------------------------------

N4 = ((0, -1), (-1, 0), (1, 0), (0, 1))
N8 = N4 + ((-1, -1), (1, -1), (-1, 1), (1, 1))


def add_outline(grid: NameGrid, color: str, *, diagonal: bool = False) -> NameGrid:
    """Add a 1-px outline in ``color`` on transparent pixels touching the figure."""

    width, height = _dimensions(grid)
    out = [row[:] for row in grid]
    around = N8 if diagonal else N4
    for y in range(height):
        for x in range(width):
            if grid[y][x] is not None:
                continue
            for dx, dy in around:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] not in (None, color):
                    out[y][x] = color
                    break
    return out


def strip_outline(grid: NameGrid, color: str) -> NameGrid:
    """Remove outline pixels that touch transparency (the outer outline only)."""

    width, height = _dimensions(grid)
    out = [row[:] for row in grid]
    for y in range(height):
        for x in range(width):
            if grid[y][x] != color:
                continue
            for dx, dy in N4:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height) or grid[ny][nx] is None:
                    out[y][x] = None
                    break
    return out


def recolor(grid: NameGrid, mapping: Mapping[str, str | None]) -> NameGrid:
    return [[mapping.get(n, n) if n is not None else None for n in row] for row in grid]


def shade(
    grid: NameGrid,
    base: str,
    *,
    highlight: str | None,
    shadow: str | None,
    light: str = "top-left",
) -> NameGrid:
    """Rim-light a region of ``base``: edges facing the light get ``highlight``,
    edges facing away get ``shadow``. The region is every ``base`` pixel."""

    lx, ly = {"top-left": (-1, -1), "top-right": (1, -1), "top": (0, -1), "left": (-1, 0)}.get(light, (-1, -1))
    width, height = _dimensions(grid)
    out = [row[:] for row in grid]

    def outside(x: int, y: int) -> bool:
        return not (0 <= x < width and 0 <= y < height) or grid[y][x] != base

    for y in range(height):
        for x in range(width):
            if grid[y][x] != base:
                continue
            toward = (lx and outside(x + lx, y)) or (ly and outside(x, y + ly))
            away = (lx and outside(x - lx, y)) or (ly and outside(x, y - ly))
            if toward and highlight and not away:
                out[y][x] = highlight
            elif away and shadow and not toward:
                out[y][x] = shadow
    return out


def orphans(grid: NameGrid) -> list[tuple[int, int, str]]:
    """Opaque pixels with no same-coloured 8-neighbour inside a region of another colour."""

    width, height = _dimensions(grid)
    found = []
    for y in range(height):
        for x in range(width):
            name = grid[y][x]
            if name is None:
                continue
            neighbours = [
                grid[y + dy][x + dx]
                for dx, dy in N8
                if 0 <= x + dx < width and 0 <= y + dy < height
            ]
            if name in neighbours:
                continue
            opaque = [n for n in neighbours if n is not None]
            if len(opaque) >= 6:
                majority = max(sorted(set(opaque)), key=opaque.count)
                found.append((x, y, majority))
    return found


def holes(grid: NameGrid) -> list[tuple[int, int, str]]:
    """Transparent pixels enclosed on all four sides by opaque pixels."""

    width, height = _dimensions(grid)
    found = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if grid[y][x] is not None:
                continue
            around = [grid[y + dy][x + dx] for dx, dy in N4]
            if all(n is not None for n in around):
                found.append((x, y, max(sorted(set(around)), key=around.count)))
    return found


def thick_lines(grid: NameGrid, color: str) -> list[tuple[int, int]]:
    """Top-left corners of 2x2 blocks of ``color``: a doubled outline."""

    width, height = _dimensions(grid)
    return [
        (x, y)
        for y in range(height - 1)
        for x in range(width - 1)
        if grid[y][x] == grid[y][x + 1] == grid[y + 1][x] == grid[y + 1][x + 1] == color
    ]


def flood(grid: NameGrid, x: int, y: int, color: str | None) -> NameGrid:
    width, height = _dimensions(grid)
    if not (0 <= x < width and 0 <= y < height):
        raise PixelTechError(f"flood point {x},{y} is outside {width}x{height}")
    out = [row[:] for row in grid]
    target = grid[y][x]
    if target == color:
        return out
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if not (0 <= cx < width and 0 <= cy < height) or out[cy][cx] != target:
            continue
        out[cy][cx] = color
        stack.extend((cx + dx, cy + dy) for dx, dy in N4)
    return out


def contact_shadow(width: int, color: str, canvas_w: int, cx: int) -> list[tuple[int, str]]:
    start = cx - width // 2
    return [(x, color) for x in range(start, start + width) if 0 <= x < canvas_w]


# ---------------------------------------------------------------------------
# pixel-rig
# ---------------------------------------------------------------------------


def _load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise _fail(source, "file not found") from exc
    except json.JSONDecodeError as exc:
        raise PixelTechError(f"{source}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc


def _round_half_away(value: float) -> int:
    return int(math.floor(abs(value) + 0.5)) * (1 if value >= 0 else -1)


@dataclass
class Rig:
    path: Path
    data: dict[str, Any]
    palette: Palette
    warnings: list[str] = field(default_factory=list)

    @property
    def root(self) -> Path:
        return self.path.parent

    @property
    def canvas(self) -> tuple[int, int]:
        return _xy(self.data["canvas"], f"{_where(self.path, _line_of(self.path, '\"canvas\"'))}: canvas")

    @property
    def origin(self) -> tuple[int, int]:
        return _xy(self.data["origin"], f"{_where(self.path, _line_of(self.path, '\"origin\"'))}: origin")

    @property
    def directions(self) -> list[str]:
        return list(self.data.get("directions", ["down", "up", "left", "right"]))

    @property
    def mirror(self) -> dict[str, str]:
        return dict(self.data.get("mirror", {}))

    @property
    def fallback(self) -> dict[str, str]:
        return dict(self.data.get("fallback", {}))

    @property
    def parts(self) -> dict[str, dict[str, Any]]:
        return self.data["parts"]

    @property
    def groups(self) -> dict[str, list[str]]:
        groups = {"all": list(self.parts)}
        groups.update(self.data.get("groups", {}))
        return groups

    def drawn_direction(self, direction: str) -> str:
        return self.mirror.get(direction, direction)

    def part_grid(
        self,
        part: str,
        direction: str,
        variant: str | None,
        base_dir: Path | None = None,
        use_fallback: bool = True,
        warn_variant: bool = True,
    ) -> Grid | None:
        """Find ``<part>.<dir>[.<variant>].txt``, falling back through variants and,
        when allowed, the rig's direction fallbacks. Layers only fall back if their
        ``layer.json`` says ``"fallback": true`` (a face must not appear on the back
        of a head)."""

        folder = base_dir or (self.root / self.data.get("part_dir", "parts"))
        tried = []
        for d in (direction, self.fallback.get(direction) if use_fallback else None):
            if not d:
                continue
            names = [f"{part}.{d}.{variant}.txt"] if variant else []
            names.append(f"{part}.{d}.txt")
            for name in names:
                candidate = folder / name
                tried.append(candidate.name)
                if candidate.exists():
                    if variant and warn_variant and not name.endswith(f".{variant}.txt"):
                        self.warnings.append(
                            f"{_where(self.path, _line_of(self.path, f'\"{part}\"'))}: "
                            f"{folder.name}/{part}: no {variant!r} variant for {d}; used the base drawing"
                        )
                    return read_grid(candidate, self.palette)
        return None

    def placement(self, part: str, direction: str) -> tuple[int, int]:
        spots = self.parts[part]
        d = direction if direction in spots else self.fallback.get(direction, direction)
        if d not in spots:
            raise _fail(
                self.path,
                f"part {part!r} has no placement for direction {direction!r}",
                line=_line_of(self.path, f'\"{part}\"'),
            )
        return _xy(spots[d], f"{_where(self.path, _line_of(self.path, f'\"{part}\"'))}: {part}.{d}")

    def draw_order(self, direction: str) -> list[str]:
        orders = self.data["draw_order"]
        d = direction if direction in orders else self.fallback.get(direction, direction)
        if d not in orders:
            raise _fail(
                self.path,
                f"no draw_order for direction {direction!r}",
                line=_line_of(self.path, '"draw_order"'),
            )
        return list(orders[d])

    def posture(self, name: str | None) -> dict[str, Any]:
        if not name:
            return {}
        postures = self.data.get("postures", {})
        if name not in postures:
            raise _fail(self.path, f"unknown posture {name!r}", line=_line_of(self.path, '"postures"'))
        spec = postures[name]
        if not isinstance(spec, Mapping):
            raise _fail(self.path, f"posture {name!r} must be an object", line=_line_of(self.path, f'"{name}"'))
        return copy.deepcopy(dict(spec))

    def prop_grid(self, name: str, direction: str) -> Grid:
        folder = self.root / self.data.get("prop_dir", "../props")
        for candidate in (folder / f"{name}.{direction}.txt", folder / f"{name}.txt"):
            if candidate.exists():
                return read_grid(candidate, self.palette)
        raise _fail(self.path, f"prop {name!r} has no drawing for direction {direction!r}")


def load_rig(path: str | Path) -> Rig:
    rig_path = Path(path)
    data = _load_json(rig_path)
    for key in ("canvas", "origin", "parts", "draw_order"):
        if key not in data:
            raise _fail(rig_path, f"missing {key!r}")
    palette_path = Path(data.get("palette", "art/palette/game.json"))
    if not palette_path.is_absolute() and not palette_path.exists():
        palette_path = rig_path.parent / palette_path
    return Rig(rig_path, data, load_palette(palette_path))


@dataclass
class Layer:
    name: str
    folder: Path
    z: str = "part"  # part | top | bottom
    mode: str = "over"  # over | replace
    paint: list[dict[str, Any]] = field(default_factory=list)
    fallback: bool = False
    asymmetric: bool = False
    all_directions: bool = False


def load_layer(rig: Rig, name: str) -> Layer:
    layers_dir = rig.root / rig.data.get("layer_dir", "layers")
    folder = layers_dir / name
    if not folder.is_dir():
        raise _fail(rig.path, f"layer {name!r} not found in {layers_dir}", line=_line_of(rig.path, '"layer_dir"'))
    meta = _load_json(folder / "layer.json") if (folder / "layer.json").exists() else {}
    return Layer(
        name,
        folder,
        meta.get("z", "part"),
        meta.get("mode", "over"),
        meta.get("paint", []),
        bool(meta.get("fallback", False)),
        bool(meta.get("asymmetric", False)),
        bool(meta.get("all_directions", False)),
    )


def load_swaps(rig: Rig) -> dict[str, dict[str, dict[str, str]]]:
    path = rig.data.get("swaps")
    if not path:
        return {}
    source = rig.root / path
    swaps = expand_swaps(_load_json(source), rig.palette)
    for group, sets in swaps.items():
        for set_name, mapping in sets.items():
            check_names([[list(mapping) + list(mapping.values())]], rig.palette, f"{source}:{group}:{set_name}")
    return swaps


def expand_swaps(swaps: Mapping[str, Any], palette: Palette) -> dict[str, dict[str, dict[str, str]]]:
    """A swap set is a colour-name map, or ``{"from_ramp": a, "to_ramp": b}`` to map
    one palette ramp onto another by position (darkest to lightest)."""

    out: dict[str, dict[str, dict[str, str]]] = {}
    for group, sets in swaps.items():
        out[group] = {}
        for set_name, spec in sets.items():
            if isinstance(spec, dict) and "from_ramp" in spec:
                try:
                    a, b = palette.ramps[spec["from_ramp"]], palette.ramps[spec["to_ramp"]]
                except KeyError as exc:
                    source = palette.source
                    raise _fail(source, f"swap {group}:{set_name}: unknown ramp {exc}") from exc
                if len(a) != len(b):
                    raise PixelTechError(f"swap {group}:{set_name}: ramps differ in length")
                out[group][set_name] = {x: y for x, y in zip(a, b) if x != y}
            else:
                out[group][set_name] = dict(spec)
    return out


def resolve_swaps(rig: Rig, picks: Sequence[str]) -> dict[str, str]:
    swaps = load_swaps(rig)
    mapping: dict[str, str] = {}
    for pick in picks:
        if ":" not in pick:
            raise PixelTechError(f"swap {pick!r} must be 'group:set'")
        group, set_name = pick.split(":", 1)
        try:
            mapping.update(swaps[group][set_name])
        except KeyError as exc:
            raise PixelTechError(f"unknown swap {pick!r}") from exc
    return mapping


def load_poses(rig: Rig, path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    source = Path(path) if path else rig.root / rig.data.get("poses", "poses.json")
    if not source.exists() and not source.is_absolute():
        source = Path(rig.data.get("poses", "poses.json"))
    data = _load_json(source)
    if not isinstance(data, Mapping) or not isinstance(data.get("poses"), Mapping):
        raise _fail(source, "expected an object containing a 'poses' object")
    return dict(data["poses"])


def expand_pose(pose: Mapping[str, Any], direction: str) -> tuple[list[dict[str, Any]], list[int]]:
    """Return the frame offset maps and holds (in 60 fps ticks) for one direction.

    A pose has ``frames`` or ``keys`` (+ ``inbetween``). ``directions`` may
    override either per direction. Tweening interpolates dx/dy and switches
    variants at the midpoint."""

    spec = dict(pose)
    spec.update(pose.get("directions", {}).get(direction, {}))
    if "keys" in spec:
        keys = spec["keys"]
        steps = int(spec.get("inbetween", 1))
        if not isinstance(keys, list) or not keys:
            raise PixelTechError("pose keys must contain at least one frame")
        if steps < 0:
            raise PixelTechError("pose inbetween must be zero or greater")
        frames: list[dict[str, Any]] = []
        for a, b in zip(keys, keys[1:]):
            frames.append(copy.deepcopy(a))
            for step in range(1, steps + 1):
                t = step / (steps + 1)
                frame: dict[str, Any] = {}
                for target in sorted(set(a) | set(b)):
                    oa, ob = a.get(target, {}), b.get(target, {})
                    entry = {
                        "dx": _round_half_away(oa.get("dx", 0) + (ob.get("dx", 0) - oa.get("dx", 0)) * t),
                        "dy": _round_half_away(oa.get("dy", 0) + (ob.get("dy", 0) - oa.get("dy", 0)) * t),
                    }
                    src = oa if t < 0.5 else ob
                    for key in ("variant", "hide"):
                        if key in src:
                            entry[key] = src[key]
                    frame[target] = entry
                frames.append(frame)
        frames.append(copy.deepcopy(keys[-1]))
    else:
        frames = copy.deepcopy(spec.get("frames", [{}]))
    if not isinstance(frames, list) or not frames:
        raise PixelTechError("pose frames must contain at least one frame")
    if any(not isinstance(frame, Mapping) for frame in frames):
        raise PixelTechError("every pose frame must be an object")
    hold = spec.get("hold", 8)
    holds = list(hold) if isinstance(hold, list) else [int(hold)] * len(frames)
    if not holds:
        raise PixelTechError("pose hold list must not be empty")
    try:
        holds = [int(value) for value in holds]
    except (TypeError, ValueError) as exc:
        raise PixelTechError("pose holds must be integers") from exc
    if len(holds) < len(frames):
        holds += [holds[-1]] * (len(frames) - len(holds))
    return frames, holds[: len(frames)]


def _part_state(
    rig: Rig,
    frame: Mapping[str, Any],
    part: str,
    default_variants: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    state = {"dx": 0, "dy": 0, "variant": (default_variants or {}).get(part), "hide": False}
    targets = [g for g, members in rig.groups.items() if part in members and g in frame]
    if part in frame:
        targets.append(part)
    for target in targets:
        entry = frame[target]
        state["dx"] += int(entry.get("dx", 0))
        state["dy"] += int(entry.get("dy", 0))
        if "variant" in entry:
            state["variant"] = entry["variant"]
        if entry.get("hide"):
            state["hide"] = True
    return state


def _paint(grid: NameGrid, rules: Sequence[Mapping[str, Any]], part: str, direction: str, variant: str | None) -> NameGrid:
    out = [row[:] for row in grid]
    for rule in rules:
        if rule.get("part") != part:
            continue
        if "directions" in rule and direction not in rule["directions"]:
            continue
        if "variant" in rule and rule["variant"] != variant:
            continue
        if "variant" not in rule and variant and rule.get("base_only"):
            continue
        y0, y1 = rule.get("rows", [0, len(out) - 1])
        x0, x1 = rule.get("cols", [0, len(out[0]) - 1])
        mapping = rule["map"]
        for y in range(max(0, y0), min(len(out) - 1, y1) + 1):
            for x in range(max(0, x0), min(len(out[0]) - 1, x1) + 1):
                name = out[y][x]
                if name is not None and name in mapping:
                    out[y][x] = mapping[name]
    return out


def compose_frame(
    rig: Rig,
    direction: str,
    frame: Mapping[str, Any],
    layers: Sequence[Layer] = (),
    swaps: Mapping[str, str] | None = None,
    *,
    part_variants: Mapping[str, str] | None = None,
    draw_shadow: bool = True,
) -> NameGrid:
    """Build one frame: parts in draw order, layers on their parts, swaps,
    outline, then the contact shadow underneath."""

    width, height = rig.canvas
    drawn = rig.drawn_direction(direction)
    canvas = blank(width, height)
    clipped: list[str] = []

    def place(sprite: Grid, part: str, state: Mapping[str, Any]) -> None:
        at_x, at_y = rig.placement(part, drawn)
        px, py = sprite.pivot
        blit(canvas, sprite.frames[0], at_x - px + state["dx"], at_y - py + state["dy"], clipped)

    top: list[tuple[Grid, str, dict[str, Any]]] = []
    bottom: list[tuple[Grid, str, dict[str, Any]]] = []
    plan: list[tuple[str, dict[str, Any], Grid | None, list[Grid]]] = []
    for part in rig.draw_order(drawn):
        state = _part_state(rig, frame, part, part_variants)
        if state["hide"]:
            continue
        base = rig.part_grid(part, drawn, state["variant"])
        if base is None:
            continue
        over: list[Grid] = []
        replace = False
        paint_rules: list[dict[str, Any]] = []
        for layer in layers:
            paint_rules.extend(layer.paint)
            drawing = rig.part_grid(
                part, drawn, state["variant"], base_dir=layer.folder,
                use_fallback=layer.fallback, warn_variant=False,
            )
            if drawing is None:
                continue
            if layer.z == "top":
                top.append((drawing, part, state))
            elif layer.z == "bottom":
                bottom.append((drawing, part, state))
            else:
                over.append(drawing)
                replace = replace or layer.mode == "replace"
        if paint_rules:
            base = Grid(base.width, base.height, [_paint(base.frames[0], paint_rules, part, drawn, state["variant"])], base.headers)
        plan.append((part, state, None if replace else base, over))

    prop_plan: list[tuple[str, Grid, int, int]] = []
    raw_props = frame.get("props", [])
    if isinstance(raw_props, Mapping):
        raw_props = [raw_props]
    if not isinstance(raw_props, Sequence) or isinstance(raw_props, (str, bytes)):
        raise PixelTechError("frame props must be an object or list")
    for prop in raw_props:
        if not isinstance(prop, Mapping):
            raise PixelTechError("every held prop must be an object")
        name = str(prop["name"])
        part = str(prop["part"])
        if part not in rig.parts:
            raise PixelTechError(f"held prop {name!r} names unknown part {part!r}")
        state = _part_state(rig, frame, part, part_variants)
        part_grid = rig.part_grid(part, drawn, state["variant"])
        if part_grid is None:
            raise PixelTechError(f"held prop {name!r} cannot find part {part!r}")
        anchor_name = str(prop.get("anchor", "hand"))
        anchor = part_grid.anchor(anchor_name)
        if anchor is None:
            raise _fail(part_grid.source, f"held prop {name!r} needs anchor-{anchor_name}")
        prop_grid = rig.prop_grid(name, drawn)
        grip = prop_grid.anchor("grip") or prop_grid.pivot
        at_x, at_y = rig.placement(part, drawn)
        part_px, part_py = part_grid.pivot
        x = at_x - part_px + anchor[0] + state["dx"] - grip[0] + int(prop.get("dx", 0))
        y = at_y - part_py + anchor[1] + state["dy"] - grip[1] + int(prop.get("dy", 0))
        prop_plan.append((str(prop.get("z", "top")), prop_grid, x, y))

    for z, drawing, x, y in prop_plan:
        if z == "bottom":
            blit(canvas, drawing.frames[0], x, y, clipped)
    for drawing, part, state in bottom:
        place(drawing, part, state)
    for part, state, base, over in plan:
        if base is not None:
            place(base, part, state)
        for drawing in over:
            place(drawing, part, state)
    for drawing, part, state in top:
        place(drawing, part, state)
    for z, drawing, x, y in prop_plan:
        if z != "bottom":
            blit(canvas, drawing.frames[0], x, y, clipped)

    if swaps:
        canvas = recolor(canvas, swaps)
    outline = rig.data.get("outline", {})
    if outline.get("mode", "outer") == "outer" and outline.get("color"):
        canvas = add_outline(canvas, outline["color"], diagonal=bool(outline.get("diagonal", False)))
    shadow = rig.data.get("shadow") if draw_shadow else None
    if shadow and shadow.get("color"):
        ox, oy = rig.origin
        widths = shadow.get("rows", [shadow.get("width", width // 2)])
        for i, w in enumerate(widths):
            y = oy + i
            if 0 <= y < height:
                for x, color in contact_shadow(int(w), shadow["color"], width, ox):
                    if canvas[y][x] is None:
                        canvas[y][x] = color
    if clipped:
        rig.warnings.append(
            f"{_where(rig.path, _line_of(rig.path, '\"canvas\"'))}: {direction}: "
            f"{len(clipped)} pixel(s) fell outside the canvas and were clipped"
        )
    if direction in rig.mirror:
        canvas = flip_h(canvas)
    return canvas


@dataclass
class Appearance:
    name: str
    layers: list[str]
    swaps: list[str]
    frame_layers: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    posture: str | None = None
    pose_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    held_props: list[dict[str, Any]] = field(default_factory=list)
    shadow: bool = True
    time_variants: dict[str, dict[str, Any]] = field(default_factory=dict)
    family_inherit: dict[str, list[str]] = field(default_factory=dict)
    selected_variant: str | None = None


def _patch_list(base: Sequence[str], patch: Any) -> list[str]:
    if isinstance(patch, list):
        return list(patch)
    if not isinstance(patch, Mapping):
        raise PixelTechError("appearance list patch must be a list or {add, remove}")
    removed = set(patch.get("remove", []))
    out = [item for item in base if item not in removed]
    out.extend(item for item in patch.get("add", []) if item not in out)
    return out


def _merge_nested(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(base))
    for key, value in patch.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
            out[key] = _merge_nested(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def apply_family(appearance: Appearance, family: Appearance | None) -> Appearance:
    """Inherit cosmetic layer prefixes and swap groups from a related look."""

    if family is None or not appearance.family_inherit:
        return appearance
    result = copy.deepcopy(appearance)
    prefixes = tuple(result.family_inherit.get("layerPrefixes", []))
    if prefixes:
        inherited = [layer for layer in family.layers if layer.startswith(prefixes)]
        result.layers = [layer for layer in result.layers if not layer.startswith(prefixes)] + inherited
    groups = set(result.family_inherit.get("swapGroups", []))
    if groups:
        inherited_swaps = [swap for swap in family.swaps if swap.split(":", 1)[0] in groups]
        result.swaps = [swap for swap in result.swaps if swap.split(":", 1)[0] not in groups] + inherited_swaps
    return result


def load_appearance(
    path: str | Path | None,
    rig: Rig,
    *,
    variant: str | None = None,
    family: Appearance | None = None,
) -> Appearance:
    if path is None:
        return Appearance("bare", [], [])
    data = _load_json(path)
    variants = data.get("timeVariants", {})
    if variant:
        if variant not in variants:
            raise _fail(path, f"unknown appearance variant {variant!r}", line=_line_of(path, '"timeVariants"'))
        patch = variants[variant]
        data = _merge_nested(data, {k: v for k, v in patch.items() if k not in {"layers", "swaps"}})
        if "layers" in patch:
            data["layers"] = _patch_list(data.get("layers", []), patch["layers"])
        if "swaps" in patch:
            data["swaps"] = _patch_list(data.get("swaps", []), patch["swaps"])
    appearance = Appearance(
        data.get("name", Path(path).stem), list(data.get("layers", [])), list(data.get("swaps", [])),
        copy.deepcopy(data.get("frameLayers", {})), data.get("posture"),
        copy.deepcopy(data.get("poseOverrides", {})), copy.deepcopy(data.get("heldProps", [])),
        bool(data.get("shadow", True)), copy.deepcopy(variants), copy.deepcopy(data.get("familyInherit", {})),
        variant,
    )
    return apply_family(appearance, family)


def _appearance_pose(rig: Rig, pose_name: str, pose: Mapping[str, Any], appearance: Appearance) -> dict[str, Any]:
    spec = copy.deepcopy(dict(pose))
    posture = rig.posture(appearance.posture)
    if pose_name in posture.get("poseOverrides", {}):
        spec = _merge_nested(spec, posture["poseOverrides"][pose_name])
    if pose_name in appearance.pose_overrides:
        spec = _merge_nested(spec, appearance.pose_overrides[pose_name])
    return spec


def _held_props_for_frame(
    held_props: Sequence[Mapping[str, Any]], pose: str, direction: str, frame_number: int,
) -> list[dict[str, Any]]:
    out = []
    for prop in held_props:
        poses = prop.get("poses", [prop.get("pose", pose)])
        directions = prop.get("directions", [direction])
        frames = prop.get("frames")
        if pose not in poses or direction not in directions:
            continue
        if frames is not None and frame_number not in frames:
            continue
        out.append({k: copy.deepcopy(v) for k, v in prop.items() if k not in {"pose", "poses", "directions", "frames"}})
    return out


def rig_frames(
    rig: Rig,
    poses: Mapping[str, Any],
    appearance: Appearance,
    extra_swaps: Sequence[str] = (),
    only_poses: Sequence[str] | None = None,
    directions: Sequence[str] | None = None,
) -> dict[tuple[str, str], tuple[list[NameGrid], list[int]]]:
    layer_names = set(appearance.layers)
    for override in appearance.frame_layers.values():
        layer_names.update(override.get("add", []))
    layer_cache = {name: load_layer(rig, name) for name in sorted(layer_names)}
    swaps = resolve_swaps(rig, list(appearance.swaps) + list(extra_swaps))
    result: dict[tuple[str, str], tuple[list[NameGrid], list[int]]] = {}
    requested_poses = set(only_poses or poses)
    unknown_poses = sorted(requested_poses - set(poses))
    if unknown_poses:
        raise _fail(rig.root / rig.data.get("poses", "poses.json"), "unknown pose(s): " + ", ".join(unknown_poses))
    requested_directions = list(directions or rig.directions)
    unknown_directions = sorted(set(requested_directions) - set(rig.directions))
    if unknown_directions:
        raise _fail(rig.path, "unknown direction(s): " + ", ".join(unknown_directions), line=_line_of(rig.path, '"directions"'))
    posture = rig.posture(appearance.posture)
    part_variants = dict(posture.get("variants", {}))
    for pose_name in sorted(poses):
        if only_poses and pose_name not in only_poses:
            continue
        for direction in requested_directions:
            pose_spec = _appearance_pose(rig, pose_name, poses[pose_name], appearance)
            frames, holds = expand_pose(pose_spec, direction)
            grids = []
            for index, frame in enumerate(frames, 1):
                frame = copy.deepcopy(frame)
                injected_props = _held_props_for_frame(appearance.held_props, pose_name, direction, index)
                if injected_props:
                    raw = frame.get("props", [])
                    frame["props"] = ([raw] if isinstance(raw, Mapping) else list(raw)) + injected_props
                names = list(appearance.layers)
                for key in (f"{pose_name}/{index}", f"{pose_name}/{direction}/{index}"):
                    override = appearance.frame_layers.get(key, {})
                    removed = set(override.get("remove", []))
                    names = [name for name in names if name not in removed]
                    names.extend(name for name in override.get("add", []) if name not in names)
                grids.append(compose_frame(
                    rig, direction, frame, [layer_cache[name] for name in names], swaps,
                    part_variants=part_variants, draw_shadow=appearance.shadow,
                ))
            result[(pose_name, direction)] = (grids, holds)
    return result


def mirror_check(rig: Rig, layer_names: Sequence[str] = ()) -> list[str]:
    """Flag drawn directional details that will be mirrored without bespoke art."""

    findings: list[str] = []
    folders = [("parts", rig.root / rig.data.get("part_dir", "parts"))]
    folders += [(f"layer {name}", load_layer(rig, name).folder) for name in layer_names]
    for target, source_direction in sorted(rig.mirror.items()):
        for label, folder in folders:
            for source in sorted(folder.glob(f"*.{source_direction}*.txt")):
                target_name = source.name.replace(f".{source_direction}", f".{target}", 1)
                explicit = folder / target_name
                if explicit.exists():
                    continue
                grid = read_grid(source, rig.palette).frames[0]
                if grid != flip_h(grid):
                    findings.append(
                        f"{_where(source, 1)}: {label} detail is asymmetric and {target!r} will mirror it; review or draw {target_name}"
                    )
    return findings


def asymmetric_layer_problems(rig: Rig, layer_names: Sequence[str] | None = None) -> list[str]:
    """Asymmetric layers must carry an explicit target-direction drawing."""

    layers_dir = rig.root / rig.data.get("layer_dir", "layers")
    if not layers_dir.is_dir():
        return []
    names = list(layer_names) if layer_names is not None else sorted(
        path.name for path in layers_dir.iterdir() if path.is_dir()
    )
    problems: list[str] = []
    for name in names:
        layer = load_layer(rig, name)
        if layer.all_directions:
            families: set[tuple[str, str | None]] = set()
            for source in layer.folder.glob("*.txt"):
                bits = source.stem.split(".")
                if len(bits) >= 2 and bits[1] in rig.directions:
                    families.add((bits[0], ".".join(bits[2:]) or None))
            for part, variant in sorted(families, key=lambda value: (value[0], value[1] or "")):
                for direction in rig.directions:
                    suffix = f".{variant}" if variant else ""
                    expected = layer.folder / f"{part}.{direction}{suffix}.txt"
                    if not expected.exists():
                        problems.append(
                            f"{_where(layer.folder / 'layer.json')}: all-directions layer {name!r} requires {expected.name}"
                        )
        if not layer.asymmetric:
            continue
        pairs = dict(rig.mirror)
        if "left" in rig.directions and "right" in rig.directions:
            pairs.setdefault("right", "left")
        for target, source_direction in sorted(pairs.items()):
            sources = sorted(layer.folder.glob(f"*.{source_direction}*.txt"))
            if not sources:
                problems.append(f"{_where(layer.folder / 'layer.json')}: asymmetric layer {name!r} has no {source_direction!r} drawing")
            for source in sources:
                target_name = source.name.replace(f".{source_direction}", f".{target}", 1)
                if not (layer.folder / target_name).exists():
                    problems.append(
                        f"{_where(layer.folder / 'layer.json')}: asymmetric layer {name!r} requires {target_name}"
                    )
    return problems


def onion_skin(
    rig: Rig,
    poses: Mapping[str, Any],
    appearance: Appearance,
    output: str | Path,
    *,
    pose: str,
    direction: str,
) -> Path:
    """Diagnostic pose strip: previous frame ghosted below the current frame."""

    frames = rig_frames(rig, poses, appearance, only_poses=[pose], directions=[direction])[(pose, direction)][0]
    panels = []
    previous = None
    for grid in frames:
        current = to_image(grid, rig.palette)
        panel = Image.new("RGBA", current.size, (40, 42, 54, 255))
        if previous is not None:
            ghost = previous.copy()
            ghost.putalpha(72)
            panel.alpha_composite(ghost)
        panel.alpha_composite(current)
        panels.append(panel)
        previous = current
    return save_png(one_and_four(sheet(panels, len(panels), gap=2)), output)


# Dialogue portraits are 64x64 (docs/pixel_art.md section 4, decision 37). The committed 48x48
# grids are legacy starters, redrawn at 64x64 in the portrait pass; until then both sizes read.
PORTRAIT_SIZE = 64
LEGACY_PORTRAIT_SIZE = 48


def portrait_grid(rig: Rig, poses: Mapping[str, Any], appearance: Appearance, *, pose: str = "idle", direction: str = "down") -> NameGrid:
    """Return a 64x64 bust grid (the sprite's top 16x16 at 4x) to redraw by hand.

    The starter only places the head and shoulders; the finished portrait is drawn over it
    with real shading (the pixel-face skill's portrait standard), never shipped as it is."""

    frame = rig_frames(rig, poses, appearance, only_poses=[pose], directions=[direction])[(pose, direction)][0][0]
    scale = PORTRAIT_SIZE // 16
    bust = [row[:16] for row in frame[:16]]
    return [[value for value in row for _ in range(scale)] for row in bust for _ in range(scale)]


def portrait_kit_grid(
    kit_dir: str | Path,
    build: str,
    layers: Sequence[str],
    palette: Palette,
    swaps: Mapping[str, str] | None = None,
) -> NameGrid:
    """Compose a hand-drawn 64x64 portrait head kit without scaling a sprite."""

    root = Path(kit_dir) / build
    base = read_grid(root / "base.txt", palette)
    n = PORTRAIT_SIZE
    if (base.width, base.height) != (n, n):
        raise _fail(base.source, f"portrait-kit base must be {n}x{n}, got {base.width}x{base.height}")
    canvas = blank(n, n)
    blit(canvas, base.frames[0], 0, 0)
    for name in layers:
        source = root / f"{name}.txt"
        layer = read_grid(source, palette)
        if (layer.width, layer.height) != (n, n):
            raise _fail(source, f"portrait-kit layer must be {n}x{n}, got {layer.width}x{layer.height}")
        blit(canvas, layer.frames[0], 0, 0)
    return recolor(canvas, swaps or {})


def rig_check(rig: Rig, poses: Mapping[str, Any]) -> list[str]:
    """Structural problems as messages; empty means the rig is complete."""

    problems: list[str] = []
    width, height = rig.canvas
    ox, oy = rig.origin
    if not (0 <= ox < width and 0 <= oy < height):
        problems.append(
            f"{_where(rig.path, _line_of(rig.path, '\"origin\"'))}: "
            f"origin {ox},{oy} is outside the {width}x{height} canvas"
        )
    for direction in rig.directions:
        drawn = rig.drawn_direction(direction)
        if direction in rig.mirror and rig.mirror[direction] not in rig.directions:
            problems.append(
                f"{_where(rig.path, _line_of(rig.path, '\"mirror\"'))}: "
                f"{direction} mirrors {rig.mirror[direction]}, which isn't a direction"
            )
            continue
        try:
            order = rig.draw_order(drawn)
        except PixelTechError as exc:
            problems.append(str(exc))
            continue
        for part in rig.parts:
            if part not in order:
                problems.append(
                    f"{_where(rig.path, _line_of(rig.path, '\"draw_order\"'))}: "
                    f"{drawn}: part {part!r} is missing from draw_order"
                )
        for part in order:
            if part not in rig.parts:
                problems.append(
                    f"{_where(rig.path, _line_of(rig.path, '\"draw_order\"'))}: "
                    f"{drawn}: draw_order names unknown part {part!r}"
                )
                continue
            try:
                rig.placement(part, drawn)
            except PixelTechError as exc:
                problems.append(str(exc))
            grid = rig.part_grid(part, drawn, None)
            if grid is None:
                problems.append(
                    f"{_where(rig.path, _line_of(rig.path, f'\"{part}\"'))}: "
                    f"{drawn}: no drawing for part {part!r}"
                )
            else:
                px, py = grid.pivot
                if not (0 <= px < grid.width and 0 <= py < grid.height):
                    problems.append(
                        f"{_where(grid.source, _line_of(grid.source, 'pivot:') if grid.source else 1)}: "
                        f"pivot {px},{py} is outside the part"
                    )
    known = set(rig.parts) | set(rig.groups)
    poses_source = rig.root / rig.data.get("poses", "poses.json")
    for name, pose in poses.items():
        for direction in rig.directions:
            try:
                frames, holds = expand_pose(pose, direction)
            except (PixelTechError, TypeError, ValueError) as exc:
                problems.append(
                    f"{_where(poses_source, _line_of(poses_source, f'\"{name}\"'))}: "
                    f"pose {name}: {exc}"
                )
                continue
            if any(h <= 0 for h in holds):
                problems.append(
                    f"{_where(poses_source, _line_of(poses_source, f'\"{name}\"'))}: "
                    f"pose {name}: holds must be positive"
                )
            for frame in frames:
                for target in frame:
                    if target == "props":
                        continue
                    if target not in known:
                        problems.append(
                            f"{_where(poses_source, _line_of(poses_source, f'\"{name}\"'))}: "
                            f"pose {name}: unknown part or group {target!r}"
                        )
    problems.extend(asymmetric_layer_problems(rig))
    return sorted(set(problems))


def build_rig(
    rig: Rig,
    poses: Mapping[str, Any],
    appearance: Appearance,
    out_dir: str | Path,
    *,
    extra_swaps: Sequence[str] = (),
    gifs: bool = True,
    only_poses: Sequence[str] | None = None,
    directions: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Write the sprite sheet, Phaser atlas + animation JSON, previews and GIFs."""

    require_pillow()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    width, height = rig.canvas
    frames_by_key = rig_frames(rig, poses, appearance, extra_swaps, only_poses, directions)
    keys = sorted(frames_by_key)
    if not keys:
        raise _fail(rig.path, "rig build selected no poses or directions")
    pad = 2
    columns = max(len(frames_by_key[k][0]) for k in keys)
    cell_w = width + pad * 2
    cell_h = height + pad * 2
    sheet_img = Image.new("RGBA", (columns * cell_w, len(keys) * cell_h), (0, 0, 0, 0))
    atlas_frames: dict[str, Any] = {}
    anims = []
    for row, key in enumerate(keys):
        grids, holds = frames_by_key[key]
        pose, direction = key
        names = []
        for col, grid in enumerate(grids):
            fx = pad + col * cell_w
            fy = pad + row * cell_h
            sheet_img.alpha_composite(to_image(grid, rig.palette), (fx, fy))
            name = f"{appearance.name}/{pose}/{direction}/{col}"
            names.append(name)
            atlas_frames[name] = {
                "frame": {"x": fx, "y": fy, "w": width, "h": height},
                "rotated": False,
                "trimmed": False,
                "spriteSourceSize": {"x": 0, "y": 0, "w": width, "h": height},
                "sourceSize": {"w": width, "h": height},
                "pivot": {"x": rig.origin[0] / width, "y": rig.origin[1] / height},
            }
        anims.append(
            {
                "key": f"{appearance.name}-{pose}-{direction}",
                "frames": [{"key": "atlas", "frame": n, "duration": round(h * 1000 / 60)} for n, h in zip(names, holds)],
                "repeat": -1 if _appearance_pose(rig, pose, poses[pose], appearance).get("loop", True) else 0,
            }
        )
        if gifs:
            durations = [round(h * 1000 / 60) for h in holds]
            images_1x = [on_background(to_image(g, rig.palette)) for g in grids]
            images_4x = [on_background(scaled(to_image(g, rig.palette), 4)) for g in grids]
            for suffix, images in (("-1x", images_1x), ("-4x", images_4x), ("", images_4x)):
                images[0].save(
                    out / f"{pose}-{direction}{suffix}.gif",
                    save_all=True,
                    append_images=images[1:],
                    duration=durations,
                    loop=0,
                    disposal=2,
                )
    save_png(sheet_img, out / "sheet.png")
    atlas = {"frames": atlas_frames, "meta": {"image": "sheet.png", "size": {"w": sheet_img.width, "h": sheet_img.height}, "scale": "1"}}
    (out / "atlas.json").write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "anims.json").write_text(json.dumps({"anims": anims}, indent=2) + "\n", encoding="utf-8")
    labelled = on_background(sheet_img)
    save_png(one_and_four(labelled), out / "sheet-preview.png")
    return {"frames": len(atlas_frames), "rows": [f"{p}/{d}" for p, d in keys], "warnings": sorted(set(rig.warnings))}


def test_sheet(
    rig: Rig,
    poses: Mapping[str, Any],
    appearances: Sequence[Appearance],
    skin_sets: Sequence[str],
    backgrounds: Sequence[Path],
    output: str | Path,
    *,
    only_poses: Sequence[str] | None = None,
    directions: Sequence[str] | None = None,
) -> Path:
    """Every appearance x skin, every pose and direction, first frames, on each
    background at 1x, plus the same at 4x. The readability proof."""

    require_pillow()
    width, height = rig.canvas
    tiles = [to_image(read_grid(p, rig.palette).frames[0], rig.palette) for p in backgrounds] or [None]
    rows: list[Image.Image] = []
    for appearance in appearances:
        for skin in skin_sets or [None]:
            frames = rig_frames(rig, poses, appearance, [skin] if skin else [], only_poses, directions)
            strip = [to_image(frames[k][0][i], rig.palette) for k in sorted(frames) for i in range(len(frames[k][0]))]
            for tile in tiles:
                band = Image.new("RGBA", (len(strip) * (width + 2), height + 4), (40, 42, 54, 255))
                if tile is not None:
                    for x in range(0, band.width, tile.width):
                        for y in range(0, band.height, tile.height):
                            band.alpha_composite(tile, (x, y))
                for i, image in enumerate(strip):
                    band.alpha_composite(image, (i * (width + 2) + 1, 2))
                rows.append(band)
    full = sheet(rows, 1, gap=2)
    big = scaled(full, 4)
    out = Image.new("RGBA", (max(full.width, big.width), full.height + big.height + 8), (40, 42, 54, 255))
    out.alpha_composite(full, (0, 0))
    out.alpha_composite(big, (0, full.height + 8))
    return save_png(out, output)


def wardrobe(
    rig: Rig,
    poses: Mapping[str, Any],
    appearances: Sequence[Appearance],
    swap_columns: Sequence[str],
    output: str | Path,
    *,
    pose: str = "idle",
    direction: str = "down",
) -> Path:
    """Appearances (rows) x swap sets (columns), one frame each, at 1x and 4x."""

    require_pillow()
    images = []
    for appearance in appearances:
        for column in swap_columns or [""]:
            picks = [c for c in column.split("+") if c]
            frames = rig_frames(rig, {pose: poses[pose]}, appearance, picks)
            images.append(to_image(frames[(pose, direction)][0][0], rig.palette))
    grid = sheet(images, max(1, len(swap_columns) or 1))
    return save_png(one_and_four(grid), output)


# ---------------------------------------------------------------------------
# pixel-refine
# ---------------------------------------------------------------------------


def _scoped(before: NameGrid, after: NameGrid, op: Mapping[str, Any], width: int, height: int, label: str) -> NameGrid:
    """Merge an op result through optional ``within`` and ``where`` selectors."""

    if "within" not in op and "where" not in op:
        return after
    if "within" in op:
        value = op["within"]
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 4:
            raise PixelTechError(f"{label}: within must be [x, y, width, height]")
        x0, y0, w, h = (int(v) for v in value)
        if w <= 0 or h <= 0:
            raise PixelTechError(f"{label}: within width and height must be positive")
    else:
        x0, y0, w, h = 0, 0, width, height
    raw_where = op.get("where")
    if raw_where is None:
        allowed = None
    elif isinstance(raw_where, str):
        allowed = {raw_where}
    elif isinstance(raw_where, Sequence):
        allowed = {None if value is None else str(value) for value in raw_where}
    else:
        raise PixelTechError(f"{label}: where must be a colour name or list")
    out = [row[:] for row in before]
    for y in range(max(0, y0), min(height, y0 + h)):
        for x in range(max(0, x0), min(width, x0 + w)):
            if allowed is None or before[y][x] in allowed:
                out[y][x] = after[y][x]
    return out


def apply_ops(
    grid: Grid,
    ops: Sequence[Mapping[str, Any]],
    palette: Palette,
    base_dir: Path,
    *,
    source: str | Path | None = None,
) -> Grid:
    """Apply a refinement recipe.

    Every op may name 1-based ``frames`` and may be selected by a ``within``
    rectangle and/or the source colours in ``where``.
    """

    if not grid.frames:
        raise _fail(grid.source, "refine input has no frames")
    frames = [[row[:] for row in f] for f in grid.frames]
    width, height = grid.width, grid.height
    for number, op in enumerate(ops, start=1):
        if not isinstance(op, Mapping):
            raise _fail(source, f"op {number} must be an object", line=number)
        kind = op.get("op")
        line = _line_of_nth(source, '"op"', number) if source else 1
        label = f"{_where(source, line)}: op {number} ({kind})"
        try:
            raw_targets = op.get("frames", range(1, len(frames) + 1))
            if isinstance(raw_targets, (str, bytes)):
                raise PixelTechError(f"{label}: frames must be a list of 1-based integers")
            targets = [int(i) - 1 for i in raw_targets]
            if not targets:
                raise PixelTechError(f"{label}: frames must not be empty")
            if kind in {"resize-canvas", "crop"}:
                if set(targets) != set(range(len(frames))):
                    raise PixelTechError(f"{label}: canvas size ops must target every frame")
                if "within" in op or "where" in op:
                    raise PixelTechError(f"{label}: canvas size ops cannot use within/where")
                nw, nh = _xy(op["size"], label)
                if nw <= 0 or nh <= 0:
                    raise PixelTechError(f"{label}: size must be positive")
                if kind == "crop":
                    x0, y0 = _xy(op.get("at", [0, 0]), label)
                else:
                    anchor = str(op.get("anchor", "bottom-center"))
                    horizontal = anchor.split("-")[-1] if "-" in anchor else "center"
                    vertical = anchor.split("-")[0] if "-" in anchor else "middle"
                    if horizontal not in {"left", "center", "right"} or vertical not in {"top", "middle", "bottom"}:
                        raise PixelTechError(f"{label}: invalid anchor {anchor!r}")
                    x0 = {"left": 0, "center": (width - nw) // 2, "right": width - nw}[horizontal]
                    y0 = {"top": 0, "middle": (height - nh) // 2, "bottom": height - nh}[vertical]
                new_frames = []
                for frame in frames:
                    canvas = blank(nw, nh)
                    blit(canvas, frame, -x0, -y0)
                    new_frames.append(canvas)
                frames, width, height = new_frames, nw, nh
                continue
            for index in targets:
                if not 0 <= index < len(frames):
                    raise PixelTechError(f"{label}: frame {index + 1} does not exist")
                before = frames[index]
                after = [row[:] for row in before]
                if kind == "recolor":
                    after = recolor(before, op["map"])
                elif kind == "swap":
                    swaps = expand_swaps(_load_json(base_dir / op["file"]), palette)
                    group, set_name = str(op["set"]).split(":", 1)
                    try:
                        mapping = swaps[group][set_name]
                    except KeyError as exc:
                        raise PixelTechError(f"{label}: unknown swap {group}:{set_name}") from exc
                    after = recolor(before, mapping)
                elif kind == "outline":
                    after = add_outline(before, op["color"], diagonal=bool(op.get("diagonal")))
                elif kind == "strip-outline":
                    after = strip_outline(before, op["color"])
                elif kind == "shade":
                    after = shade(before, op["color"], highlight=op.get("highlight"), shadow=op.get("shadow"), light=op.get("light", "top-left"))
                elif kind in {"orphans", "holes"}:
                    finder = orphans if kind == "orphans" else holes
                    for x, y, majority in finder(before):
                        after[y][x] = majority
                elif kind == "patch":
                    patch = read_grid(base_dir / op["file"], palette)
                    ax, ay = _xy(op.get("at", [0, 0]), label)
                    patch_frame = patch.frames[min(index, len(patch.frames) - 1)]
                    blit(after, patch_frame, ax, ay)
                elif kind in {"erase", "fill-rect"}:
                    rect = op["rect"]
                    if not isinstance(rect, Sequence) or isinstance(rect, (str, bytes)) or len(rect) != 4:
                        raise PixelTechError(f"{label}: rect must be [x, y, width, height]")
                    x0, y0, w, h = (int(v) for v in rect)
                    if w <= 0 or h <= 0:
                        raise PixelTechError(f"{label}: rect width and height must be positive")
                    fill = None if kind == "erase" else op["color"]
                    for y in range(max(0, y0), min(height, y0 + h)):
                        for x in range(max(0, x0), min(width, x0 + w)):
                            after[y][x] = fill
                elif kind == "flood":
                    x, y = _xy(op["at"], label)
                    after = flood(before, x, y, op.get("color"))
                elif kind == "pixels":
                    for entry in op["set"]:
                        if not isinstance(entry, Sequence) or isinstance(entry, (str, bytes)) or len(entry) != 3:
                            raise PixelTechError(f"{label}: each pixel must be [x, y, colour]")
                        x, y = _xy(entry[:2], label)
                        if not (0 <= x < width and 0 <= y < height):
                            raise PixelTechError(f"{label}: pixel {x},{y} is outside {width}x{height}")
                        after[y][x] = entry[2]
                elif kind == "shift":
                    after = blank(width, height)
                    blit(after, before, int(op.get("dx", 0)), int(op.get("dy", 0)))
                elif kind == "flip":
                    axis = op.get("axis", "h")
                    if axis not in {"h", "v"}:
                        raise PixelTechError(f"{label}: flip axis must be 'h' or 'v'")
                    after = flip_h(before) if axis == "h" else list(reversed([row[:] for row in before]))
                else:
                    raise PixelTechError(f"{label}: unknown op {kind!r}")
                frames[index] = _scoped(before, after, op, width, height, label)
        except PixelTechError:
            raise
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise PixelTechError(f"{label}: invalid arguments: {exc}") from exc
    check_names(frames, palette, f"{_where(source)}: refine result")
    headers = dict(grid.headers)
    headers["size"] = f"{width}x{height}"
    return Grid(width, height, frames, headers, grid.comments, grid.source)


def diff_preview(before: Grid, after: Grid, palette: Palette, output: str | Path, scale: int = 6) -> Path:
    """Before | after | changed pixels (magenta), each frame, at ``scale``."""

    require_pillow()
    panels = []
    for index in range(max(len(before.frames), len(after.frames))):
        b = before.frames[min(index, len(before.frames) - 1)]
        a = after.frames[min(index, len(after.frames) - 1)]
        bi, ai = on_background(to_image(b, palette)), on_background(to_image(a, palette))
        mask = on_background(to_image(a, palette)).convert("RGBA")
        for y in range(min(len(a), len(b))):
            for x in range(min(len(a[0]), len(b[0]))):
                if a[y][x] != b[y][x]:
                    mask.putpixel((x, y), (255, 0, 200, 255))
        panels += [scaled(bi, scale), scaled(ai, scale), scaled(mask, scale)]
    return save_png(sheet(panels, 3, gap=4), output)


# ---------------------------------------------------------------------------
# pixel-cleanup
# ---------------------------------------------------------------------------


def detect_scale(image: "Image.Image") -> tuple[int, int, int]:
    """Return (scale, offset_x, offset_y) of an upscaled pixel-art image."""

    require_pillow()
    img = image.convert("RGBA")
    px = img.load()
    runs: list[int] = []
    starts_x: list[int] = []
    starts_y: list[int] = []
    for y in range(img.height):
        run, start = 1, 0
        for x in range(1, img.width + 1):
            if x < img.width and px[x, y] == px[x - 1, y]:
                run += 1
                continue
            if start > 0 and x < img.width:
                runs.append(run)
                starts_x.append(start)
            run, start = 1, x
    for x in range(img.width):
        run, start = 1, 0
        for y in range(1, img.height + 1):
            if y < img.height and px[x, y] == px[x, y - 1]:
                run += 1
                continue
            if start > 0 and y < img.height:
                runs.append(run)
                starts_y.append(start)
            run, start = 1, y
    if not runs:
        return 1, 0, 0
    scale = reduce(math.gcd, runs)
    if scale <= 1:
        return 1, 0, 0

    def phase(starts: list[int]) -> int:
        if not starts:
            return 0
        counts: dict[int, int] = {}
        for s in starts:
            counts[s % scale] = counts.get(s % scale, 0) + 1
        return max(sorted(counts), key=counts.get)

    return scale, phase(starts_x), phase(starts_y)


def unzoom(image: "Image.Image", scale: int | None = None) -> tuple["Image.Image", int]:
    require_pillow()
    img = image.convert("RGBA")
    found, ox, oy = detect_scale(img)
    scale = scale or found
    if scale <= 1:
        return img, 1
    cols = (img.width - ox) // scale
    rows = (img.height - oy) // scale
    out = Image.new("RGBA", (cols, rows))
    for y in range(rows):
        for x in range(cols):
            out.putpixel((x, y), img.getpixel((ox + x * scale + scale // 2, oy + y * scale + scale // 2)))
    return out, scale


def remove_background(image: "Image.Image", tolerance: int = 0) -> "Image.Image":
    """Make the flat colour touching the border transparent (flood fill from the edges)."""

    require_pillow()
    img = image.convert("RGBA")
    w, h = img.size
    if w <= 0 or h <= 0:
        raise PixelTechError("image is empty")
    if tolerance < 0:
        raise PixelTechError("background tolerance cannot be negative")
    px = img.load()
    border = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] + [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
    target = max(sorted(set(border)), key=border.count)

    def close(c) -> bool:
        return all(abs(c[i] - target[i]) <= tolerance for i in range(3)) and c[3] > 0

    seen = set()
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not close(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def reduce_colors(frames: Sequence[NameGrid], palette: Palette, maximum: int, keep: Sequence[str] = ()) -> list[NameGrid]:
    if maximum <= 0:
        raise PixelTechError("maximum colours must be positive")
    unknown = sorted(set(keep) - set(palette.by_name))
    if unknown:
        raise PixelTechError("unknown keep colour(s): " + ", ".join(unknown))
    counts: dict[str, int] = {}
    for f in frames:
        for row in f:
            for n in row:
                if n:
                    counts[n] = counts.get(n, 0) + 1
    ranked = sorted(counts, key=lambda n: (-counts[n], n))
    kept = list(dict.fromkeys(list(keep) + ranked))[:maximum]
    subset = Palette(palette.name, tuple(c for c in palette.colors if c.name in kept))
    known = palette.by_name
    mapping = {n: (n if n in kept else _nearest_color(known[n].rgba[:3], subset).name) for n in counts}
    return [recolor(f, mapping) for f in frames]


def lint(grid: Grid, outline: str | None = None) -> list[str]:
    messages = []
    for index, f in enumerate(grid.frames, start=1):
        for x, y, _ in orphans(f):
            messages.append(f"frame {index}: isolated pixel at {x},{y} ({f[y][x]})")
        for x, y, _ in holes(f):
            messages.append(f"frame {index}: pinhole at {x},{y}")
        if outline:
            for x, y in thick_lines(f, outline):
                messages.append(f"frame {index}: doubled {outline} line at {x},{y}")
    return messages


# ---------------------------------------------------------------------------
# pixel-tileset
# ---------------------------------------------------------------------------

# Bits: N=1, E=2, S=4, W=8, NE=16, SE=32, SW=64, NW=128 (1 = same terrain).
DIRS = {"N": (0, -1, 1), "E": (1, 0, 2), "S": (0, 1, 4), "W": (-1, 0, 8), "NE": (1, -1, 16), "SE": (1, 1, 32), "SW": (-1, 1, 64), "NW": (-1, -1, 128)}


def canonical_mask(mask: int) -> int:
    """Clear diagonal bits whose two neighbouring sides aren't both set (the 47-blob rule)."""

    for diag, (a, b) in {"NE": ("N", "E"), "SE": ("S", "E"), "SW": ("S", "W"), "NW": ("N", "W")}.items():
        if not (mask & DIRS[a][2] and mask & DIRS[b][2]):
            mask &= ~DIRS[diag][2]
    return mask


def autotile(source: Grid, tile: int = 16) -> tuple[list[NameGrid], dict[int, int]]:
    """Build the 47 blob tiles from a 4x3-tile source.

    Source layout (tile units): columns 0-2 x rows 0-2 are a 3x3 framed patch
    (outer corners, edges, centre fill); column 3 row 0 holds the four inner
    corners in its quadrants (TL quadrant = the concave corner that opens to
    the top-left, and so on). Each output tile is assembled from four
    half-size quadrants chosen by the neighbour mask."""

    if tile <= 0 or tile % 2:
        raise PixelTechError("autotile size must be a positive even integer")
    if not source.frames:
        raise _fail(source.source, "autotile source has no frames")
    half = tile // 2
    if source.width < 4 * tile or source.height < 3 * tile:
        raise PixelTechError(f"autotile source must be at least {4 * tile}x{3 * tile}")
    src = source.frames[0]

    def quad(tx: int, ty: int, qx: int, qy: int) -> NameGrid:
        x0, y0 = tx * tile + qx * half, ty * tile + qy * half
        return [row[x0 : x0 + half] for row in src[y0 : y0 + half]]

    # For quadrant (qx, qy), the orthogonal neighbours to look at and the source tiles.
    def pick(mask: int, qx: int, qy: int) -> NameGrid:
        vert = "N" if qy == 0 else "S"
        horz = "W" if qx == 0 else "E"
        diag = ("N" if qy == 0 else "S") + ("W" if qx == 0 else "E")
        diag = {"NW": "NW", "NE": "NE", "SW": "SW", "SE": "SE"}[diag]
        v = bool(mask & DIRS[vert][2])
        h = bool(mask & DIRS[horz][2])
        d = bool(mask & DIRS[diag][2])
        cx = 0 if qx == 0 else 2
        cy = 0 if qy == 0 else 2
        if v and h and d:
            return quad(1, 1, qx, qy)  # fill
        if v and h:
            return quad(3, 0, qx, qy)  # inner corner
        if not v and not h:
            return quad(cx, cy, qx, qy)  # outer corner
        if not v:
            return quad(1, cy, qx, qy)  # top/bottom edge
        return quad(cx, 1, qx, qy)  # left/right edge

    masks = sorted({canonical_mask(m) for m in range(256)})
    tiles: list[NameGrid] = []
    index_of: dict[int, int] = {}
    for m in masks:
        t = blank(tile, tile)
        for qy in (0, 1):
            for qx in (0, 1):
                blit(t, pick(m, qx, qy), qx * half, qy * half)
        index_of[m] = len(tiles)
        tiles.append(t)
    lookup = {m: index_of[canonical_mask(m)] for m in range(256)}
    return tiles, lookup


SAMPLE_MAP = [
    "............",
    ".####.......",
    ".#####..###.",
    ".##.##..###.",
    ".#####......",
    "...##...#...",
    "........##..",
    "............",
]


def autotile_sample(tiles: Sequence[NameGrid], lookup: Mapping[int, int], filler: NameGrid | None, tile: int, pattern: Sequence[str] = SAMPLE_MAP) -> NameGrid:
    if not pattern or not pattern[0] or any(len(row) != len(pattern[0]) for row in pattern):
        raise PixelTechError("autotile sample pattern must be a non-empty rectangle")
    h, w = len(pattern), len(pattern[0])
    canvas = blank(w * tile, h * tile)
    for y in range(h):
        for x in range(w):
            if pattern[y][x] != "#":
                if filler is not None:
                    blit(canvas, filler, x * tile, y * tile)
                continue
            mask = 0
            for dx, dy, bit in DIRS.values():
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and pattern[ny][nx] == "#":
                    mask |= bit
            if filler is not None:
                blit(canvas, filler, x * tile, y * tile)
            blit(canvas, tiles[lookup[mask]], x * tile, y * tile)
    return canvas


def seam_report(grid: Grid) -> list[str]:
    """Warn about solid border lines (they draw a grid when tiled) and edge breaks."""

    if not grid.frames:
        raise _fail(grid.source, "seam input has no frames")
    f = grid.frames[0]
    _dimensions(f, "seam input")
    h, w = len(f), len(f[0])
    notes = []
    edges = {"top": f[0], "bottom": f[-1], "left": [r[0] for r in f], "right": [r[-1] for r in f]}
    for side, line in edges.items():
        if len(set(line)) == 1 and line[0] is not None:
            notes.append(f"{side} edge is one solid colour ({line[0]}): it will draw a grid line when tiled")
    wrap_h = sum(1 for r in f if r[0] != r[-1])
    wrap_v = sum(1 for x in range(w) if f[0][x] != f[-1][x])
    notes.append(f"left/right edges differ on {wrap_h}/{h} rows; top/bottom on {wrap_v}/{w} columns (review the tiled preview)")
    return notes


# ---------------------------------------------------------------------------
# pixel-nineslice
# ---------------------------------------------------------------------------


def nineslice(grid: NameGrid, insets: tuple[int, int, int, int], width: int, height: int) -> NameGrid:
    """Build a panel of any size by tiling (never stretching) the edges and centre."""

    left, top, right, bottom = insets
    sw, sh = _dimensions(grid, "nine-slice source")
    if min(insets) < 0:
        raise PixelTechError("slice insets cannot be negative")
    if left + right >= sw or top + bottom >= sh:
        raise PixelTechError("slice insets leave no middle to tile")
    if width < left + right or height < top + bottom:
        raise PixelTechError(f"{width}x{height} is smaller than the fixed corners")
    mid_w, mid_h = sw - left - right, sh - top - bottom
    out = blank(width, height)

    def src_x(x: int) -> int:
        if x < left:
            return x
        if x >= width - right:
            return sw - (width - x)
        return left + (x - left) % mid_w

    def src_y(y: int) -> int:
        if y < top:
            return y
        if y >= height - bottom:
            return sh - (height - y)
        return top + (y - top) % mid_h

    for y in range(height):
        for x in range(width):
            out[y][x] = grid[src_y(y)][src_x(x)]
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _palette(args: argparse.Namespace) -> Palette:
    return load_palette(args.palette)


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_rig_check(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    problems = rig_check(rig, poses)
    for layer_name in args.layer or []:
        load_layer(rig, layer_name)
    for p in problems:
        print(f"error: {p}")
    for w in sorted(set(rig.warnings)):
        print(f"warning: {w}")
    print("rig ok" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_rig_build(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    problems = rig_check(rig, poses)
    if problems:
        for p in problems:
            print(f"error: {p}")
        return 1
    family = load_appearance(args.family_appearance, rig) if args.family_appearance else None
    appearance = load_appearance(args.appearance, rig, variant=args.variant, family=family)
    report = build_rig(
        rig, poses, appearance, args.out_dir,
        extra_swaps=args.swap or [], gifs=not args.no_gif,
        only_poses=args.only_pose or None, directions=args.direction or None,
    )
    _print(report)
    return 0


def cmd_rig_test_sheet(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    appearances = [load_appearance(a, rig) for a in args.appearance] or [load_appearance(None, rig)]
    print(test_sheet(
        rig, poses, appearances, args.skin or [], [Path(b) for b in args.background or []], args.output,
        only_poses=args.only_pose or None, directions=args.direction or None,
    ))
    return 0


def cmd_rig_wardrobe(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    appearances = [load_appearance(a, rig) for a in args.appearance] or [load_appearance(None, rig)]
    print(wardrobe(rig, poses, appearances, args.column or [], args.output, pose=args.pose, direction=args.direction))
    return 0


def cmd_rig_mirror_check(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    findings = mirror_check(rig, args.layer or [])
    for finding in findings:
        print(f"warning: {finding}")
    print(f"{len(findings)} mirrored asymmetric detail(s)")
    return 1 if findings else 0


def cmd_rig_onion(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    family = load_appearance(args.family_appearance, rig) if args.family_appearance else None
    appearance = load_appearance(args.appearance, rig, variant=args.variant, family=family)
    print(onion_skin(rig, poses, appearance, args.output, pose=args.pose, direction=args.direction))
    return 0


def cmd_rig_portrait(args: argparse.Namespace) -> int:
    rig = load_rig(args.rig)
    poses = load_poses(rig, args.poses)
    family = load_appearance(args.family_appearance, rig) if args.family_appearance else None
    appearance = load_appearance(args.appearance, rig, variant=args.variant, family=family)
    grid = portrait_grid(rig, poses, appearance, pose=args.pose, direction=args.direction)
    headers = {"category": "portrait", "origin": "24,45", "semantic": "skin"}
    output = Path(args.output_grid)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_frames([grid], rig.palette, headers, ["# 3x rig bust starter; hand-finish before production use."]), encoding="utf-8")
    if args.preview:
        save_png(one_and_four(on_background(to_image(grid, rig.palette))), args.preview)
    print(output)
    return 0


def cmd_rig_portrait_kit(args: argparse.Namespace) -> int:
    palette = _palette(args)
    mapping: dict[str, str] = {}
    if args.swap:
        if not args.swaps:
            raise PixelTechError("--swap requires --swaps")
        expanded = expand_swaps(_load_json(args.swaps), palette)
        for pick in args.swap:
            if ":" not in pick:
                raise PixelTechError(f"swap {pick!r} must be 'group:set'")
            group, set_name = pick.split(":", 1)
            try:
                mapping.update(expanded[group][set_name])
            except KeyError as exc:
                raise PixelTechError(f"unknown swap {pick!r}") from exc
    grid = portrait_kit_grid(args.kit_dir, args.build, args.layer or [], palette, mapping)
    output = Path(args.output_grid)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        format_frames([grid], palette, {"category": "portrait", "origin": "24,45", "semantic": "skin"},
                      ["# Hand-drawn portrait-kit composition; not scaled from the overworld sprite."]),
        encoding="utf-8",
    )
    if args.preview:
        save_png(one_and_four(on_background(to_image(grid, palette))), args.preview)
    print(output)
    return 0


def _face_kit(kit_dir: str):
    import face_kit  # imported lazily: face_kit imports this module

    return face_kit.FaceKit(kit_dir)


def _face_spec(args: argparse.Namespace) -> dict[str, str | bool]:
    spec: dict[str, str | bool] = {}
    if args.face:
        spec.update(_face_kit(args.kit).faces()[args.face])
    if args.head is not None:
        spec["head"] = args.head
    for part in ("eyes", "brows", "nose", "mouth", "marks", "glasses", "stubble", "beard", "moustache", "age-lines"):
        value = getattr(args, part.replace("-", "_"), None)
        if value is not None:
            spec[part] = value if value != "off" else False
    return spec


def _swap_pick(value: str, group: str) -> str:
    return value.split(":", 1)[1] if ":" in value else value


def cmd_face_compose(args: argparse.Namespace) -> int:
    kit = _face_kit(args.kit)
    spec = _face_spec(args)
    skin, hair = _swap_pick(args.skin, "skin"), _swap_pick(args.hair, "hair")
    grid = kit.compose(
        args.build, args.direction, spec,
        skin=skin, hair=hair, appearance=args.appearance or "", context=args.context,
    )
    headers = {"pivot": kit.head_pivot(args.build, args.direction), "semantic": "skin"}
    comment = f"face-compose {args.build}/{args.direction}: skin {skin}, hair {hair}."
    if args.output_grid:
        output = Path(args.output_grid)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(format_frames([grid], kit.palette, headers, [f"# {comment}"]), encoding="utf-8")
    if args.write_layer:
        folder = kit.write_layer(
            Path(args.rig_root), args.build, args.write_layer, spec,
            skin=skin, hair=hair, appearance=args.appearance or "", context=args.context,
        )
        print(f"wrote layer {folder}")
    if args.preview:
        preview = Path(args.preview)
        preview.parent.mkdir(parents=True, exist_ok=True)
        save_png(one_and_four(to_image(grid, kit.palette)), preview)
    if not args.output_grid and not args.preview and not args.write_layer:
        raise PixelTechError("face-compose needs --output-grid, --preview or --write-layer")
    print(comment)
    return 0


def cmd_face_sheet(args: argparse.Namespace) -> int:
    import face_kit as face_sheet_module

    kit = _face_kit(args.kit)
    skins = [_swap_pick(value, "skin") for value in (args.skin or ["skin:light", "skin:medium", "skin:dark", "skin:deep"])]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    face_sheet_module.face_sheet(
        kit, output, skins=skins,
        carpets=[Path(path) for path in (args.carpet or [])] or None,
        carpet_faces=args.carpet_face,
    )
    if args.directions:
        directions_output = Path(args.directions_output or output.parent / "face-kit-directions.png")
        face_sheet_module.directions_sheet(kit, directions_output, face_name=args.directions)
        print(f"wrote {directions_output}")
    print(f"wrote {output}")
    return 0


def cmd_refine(args: argparse.Namespace) -> int:
    palette = _palette(args)
    before = read_grid(args.source, palette)
    if args.recipe:
        ops = _load_json(args.recipe)
        base = Path(args.recipe).parent
        recipe_source: str | Path | None = args.recipe
    else:
        try:
            ops = json.loads(args.ops)
        except json.JSONDecodeError as exc:
            raise PixelTechError(f"<ops>:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc
        base = Path(".")
        recipe_source = None
    if isinstance(ops, dict):
        ops = ops.get("ops", [])
    if not isinstance(ops, list):
        raise _fail(recipe_source, "refine recipe must be a list or an object with an 'ops' list")
    after = apply_ops(before, ops, palette, base, source=recipe_source)
    output = Path(args.output or args.source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_frames(after.frames, palette, after.headers, after.comments), encoding="utf-8")
    if args.preview:
        diff_preview(before, after, palette, args.preview)
    print(output)
    return 0


def cmd_unzoom(args: argparse.Namespace) -> int:
    require_pillow()
    palette = _palette(args)
    image = Image.open(args.image)
    if args.remove_background:
        image = remove_background(image, args.tolerance)
    small, scale = unzoom(image, args.scale)
    grid = from_image(small, palette, nearest=True)
    headers = {"category": args.category} if args.category else {}
    Path(args.output_grid).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_grid).write_text(format_frames([grid], palette, headers, [f"# Unzoomed from {Path(args.image).name} at {scale}x."]), encoding="utf-8")
    if args.preview:
        save_png(one_and_four(on_background(to_image(grid, palette))), args.preview)
    print(f"scale {scale}x -> {small.width}x{small.height}: {args.output_grid}")
    return 0


def cmd_remove_bg(args: argparse.Namespace) -> int:
    require_pillow()
    out = remove_background(Image.open(args.image), args.tolerance)
    print(save_png(out, args.output))
    return 0


def cmd_reduce(args: argparse.Namespace) -> int:
    palette = _palette(args)
    grid = read_grid(args.source, palette)
    frames = reduce_colors(grid.frames, palette, args.max, args.keep or [])
    Path(args.output).write_text(format_frames(frames, palette, grid.headers, grid.comments), encoding="utf-8")
    print(args.output)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    palette = _palette(args)
    grid = read_grid(args.source, palette)
    messages = lint(grid, args.outline)
    for m in messages:
        print(f"warning: {m}")
    print(f"{len(messages)} finding(s)")
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    palette = _palette(args)
    grid = read_grid(args.source, palette)
    after = apply_ops(grid, [{"op": "orphans"}, {"op": "holes"}], palette, Path("."))
    Path(args.output or args.source).write_text(format_frames(after.frames, palette, after.headers, after.comments), encoding="utf-8")
    if args.preview:
        diff_preview(grid, after, palette, args.preview)
    print(args.output or args.source)
    return 0


def cmd_autotile(args: argparse.Namespace) -> int:
    palette = _palette(args)
    source = read_grid(args.source, palette)
    tile = args.tile
    tiles, lookup = autotile(source, tile)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    columns = 8
    rows = math.ceil(len(tiles) / columns)
    atlas = blank(columns * tile, rows * tile)
    for i, t in enumerate(tiles):
        blit(atlas, t, (i % columns) * tile, (i // columns) * tile)
    save_png(to_image(atlas, palette), out / "tileset.png")
    (out / "tileset.json").write_text(
        json.dumps({"tile": tile, "columns": columns, "count": len(tiles), "bits": {k: v[2] for k, v in DIRS.items()}, "maskToTile": {str(m): i for m, i in lookup.items()}}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    masks_by_index = [0] * len(tiles)
    for mask, index in lookup.items():
        canonical = canonical_mask(mask)
        if mask == canonical:
            masks_by_index[index] = mask
    tiled = {
        "type": "tileset", "version": "1.10", "tiledversion": "1.10.2",
        "name": Path(args.source).stem, "tilewidth": tile, "tileheight": tile,
        "tilecount": len(tiles), "columns": columns,
        "image": "tileset.png", "imagewidth": columns * tile, "imageheight": rows * tile,
        "tiles": [
            {"id": index, "properties": [{"name": "neighborMask", "type": "int", "value": mask}]}
            for index, mask in enumerate(masks_by_index)
        ],
        "wangsets": [{
            "name": "terrain", "tile": -1,
            "wangcolors": [{"name": "terrain", "color": "#224656", "tile": -1, "probability": 1}],
            "wangtiles": [
                {"tileid": index, "wangid": [1 if mask & DIRS[name][2] else 0 for name in ("NW", "N", "NE", "E", "SE", "S", "SW", "W")]}
                for index, mask in enumerate(masks_by_index)
            ],
        }],
    }
    (out / "tileset.tsj").write_text(json.dumps(tiled, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    filler = read_grid(args.filler, palette).frames[0] if args.filler else None
    sample = autotile_sample(tiles, lookup, filler, tile)
    save_png(one_and_four(on_background(to_image(sample, palette))), out / "sample-map.png")
    save_png(one_and_four(on_background(to_image(atlas, palette))), out / "tileset-preview.png")
    print(f"{len(tiles)} tiles -> {out}")
    return 0


def cmd_seams(args: argparse.Namespace) -> int:
    palette = _palette(args)
    grid = read_grid(args.source, palette)
    for note in seam_report(grid):
        print(f"note: {note}")
    if args.preview:
        f = grid.frames[0]
        tiled = blank(grid.width * 4, grid.height * 4)
        for y in range(4):
            for x in range(4):
                blit(tiled, f, x * grid.width, y * grid.height)
        save_png(one_and_four(on_background(to_image(tiled, palette))), args.preview)
    return 0


def cmd_nineslice(args: argparse.Namespace) -> int:
    palette = _palette(args)
    grid = read_grid(args.source, palette)
    if args.frame_ms <= 0:
        raise PixelTechError("frame-ms must be positive")
    insets = tuple(int(v) for v in (args.slice or grid.headers.get("slice", "")).split(","))
    if len(insets) != 4:
        raise PixelTechError("give --slice left,top,right,bottom or a 'slice:' header")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = Path(args.source).stem
    save_png(to_image(grid.frames[0], palette), out / f"{name}.png")
    left, top, right, bottom = insets
    (out / f"{name}.json").write_text(
        json.dumps({"key": name, "leftWidth": left, "topHeight": top, "rightWidth": right, "bottomHeight": bottom, "mode": "tile", "frames": len(grid.frames)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sizes = [tuple(int(v) for v in size.lower().split("x")) for size in args.size or ["48x32", "96x40", "160x64"]]
    preview_frames = []
    for frame in grid.frames:
        panels = [on_background(to_image(nineslice(frame, insets, w, h), palette)) for w, h in sizes]
        preview_frames.append(one_and_four(sheet(panels, 1, gap=4)))
    save_png(preview_frames[0], out / f"{name}-preview.png")
    if len(grid.frames) > 1:
        source_sheet = Image.new("RGBA", (grid.width * len(grid.frames), grid.height), (0, 0, 0, 0))
        for index, frame in enumerate(grid.frames):
            source_sheet.alpha_composite(to_image(frame, palette), (index * grid.width, 0))
        save_png(source_sheet, out / f"{name}-frames.png")
        preview_frames[0].save(
            out / f"{name}-preview.gif", save_all=True, append_images=preview_frames[1:],
            duration=args.frame_ms, loop=0, disposal=2,
        )
        (out / f"{name}-anims.json").write_text(json.dumps({
            "key": f"{name}-blink", "frameCount": len(grid.frames), "frameMs": args.frame_ms, "repeat": -1,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out / f"{name}.json")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pixel_tech", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pal = {"default": "art/palette/game.json", "help": "palette JSON (default: art/palette/game.json)"}

    p = sub.add_parser("rig-check", help="check a rig, its poses and layers")
    p.add_argument("rig")
    p.add_argument("--poses")
    p.add_argument("--layer", action="append")
    p.set_defaults(func=cmd_rig_check)

    p = sub.add_parser("rig-build", help="build sheet, atlas, animations, GIFs for one appearance")
    p.add_argument("rig")
    p.add_argument("--appearance")
    p.add_argument("--variant", help="named time variant from the appearance")
    p.add_argument("--family-appearance", help="inherit configured cosmetic choices from this appearance")
    p.add_argument("--poses")
    p.add_argument("--swap", action="append", help="extra swap, group:set")
    p.add_argument("--only-pose", action="append", help="build only this pose (repeatable)")
    p.add_argument("--direction", action="append", help="build only this direction (repeatable)")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--no-gif", action="store_true")
    p.set_defaults(func=cmd_rig_build)

    p = sub.add_parser("rig-test-sheet", help="every pose on every background, 1x and 4x")
    p.add_argument("rig")
    p.add_argument("--appearance", action="append", default=[])
    p.add_argument("--skin", action="append", help="swap per row, group:set")
    p.add_argument("--background", action="append", help="tile grid to stand on")
    p.add_argument("--poses")
    p.add_argument("--only-pose", action="append", help="show only this pose (repeatable)")
    p.add_argument("--direction", action="append", help="show only this direction (repeatable)")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_rig_test_sheet)

    p = sub.add_parser("rig-wardrobe", help="appearances x swap sets matrix")
    p.add_argument("rig")
    p.add_argument("--appearance", action="append", default=[])
    p.add_argument("--column", action="append", help="swaps for a column, joined with +")
    p.add_argument("--pose", default="idle")
    p.add_argument("--direction", default="down")
    p.add_argument("--poses")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_rig_wardrobe)

    p = sub.add_parser("rig-mirror-check", help="flag asymmetric details before mirrored directions are built")
    p.add_argument("rig")
    p.add_argument("--layer", action="append", help="also inspect this layer (repeatable)")
    p.set_defaults(func=cmd_rig_mirror_check)

    p = sub.add_parser("rig-onion-skin", help="preview consecutive pose frames overlaid")
    p.add_argument("rig")
    p.add_argument("--appearance")
    p.add_argument("--variant", help="named time variant from the appearance")
    p.add_argument("--family-appearance", help="inherit configured cosmetic choices from this appearance")
    p.add_argument("--poses")
    p.add_argument("--pose", required=True)
    p.add_argument("--direction", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_rig_onion)

    p = sub.add_parser("rig-portrait", help="make a 64x64 4x bust starter grid to redraw by hand")
    p.add_argument("rig")
    p.add_argument("--appearance")
    p.add_argument("--variant", help="named time variant from the appearance")
    p.add_argument("--family-appearance", help="inherit configured cosmetic choices from this appearance")
    p.add_argument("--poses")
    p.add_argument("--pose", default="idle")
    p.add_argument("--direction", default="down")
    p.add_argument("--output-grid", required=True)
    p.add_argument("--preview")
    p.set_defaults(func=cmd_rig_portrait)

    p = sub.add_parser("rig-portrait-kit", help="compose a hand-drawn 64x64 portrait head kit")
    p.add_argument("--kit-dir", required=True)
    p.add_argument("--build", required=True)
    p.add_argument("--layer", action="append", help="layer path below the build, without .txt")
    p.add_argument("--swaps", help="swap-set JSON")
    p.add_argument("--swap", action="append", help="swap, group:set")
    p.add_argument("--output-grid", required=True)
    p.add_argument("--preview")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_rig_portrait_kit)

    p = sub.add_parser("face-compose", help="snap hand-drawn face parts onto a kit head")
    p.add_argument("--kit", required=True, help="face-kit directory (kit.json)")
    p.add_argument("--build", required=True, help="body-a or body-b")
    p.add_argument("--direction", default="down", choices=["down", "up", "left", "right"])
    p.add_argument("--face", help="a named face combination from kit.json")
    p.add_argument("--head", help="head shape (round, long, square-jaw, narrow-chin)")
    p.add_argument("--eyes", help="eye style (dot, tall, tired, hooded, narrow, closed, white-side)")
    p.add_argument("--brows", help="brow shape (flat, arched, angled-stern, thick, sparse), or 'off'")
    p.add_argument("--nose", help="nose style (dot, long, broad), or 'off'")
    p.add_argument("--mouth", help="neutral mouth style; smile and displeased are reserved")
    p.add_argument("--marks", help="small mark style (lid, eye bag, cheek, blush, freckles, mole, ear shade)")
    p.add_argument("--glasses", help="glasses style")
    p.add_argument("--stubble", help="stubble style")
    p.add_argument("--beard", help="beard style")
    p.add_argument("--moustache", help="moustache style (reserved: Joe, Winston)")
    p.add_argument("--age-lines", help="age-lines style")
    p.add_argument("--skin", default="skin:light", help="skin swap, group:set (default skin:light)")
    p.add_argument("--hair", default="hair:black", help="hair swap, group:set (default hair:black)")
    p.add_argument("--appearance", default="", help="appearance name, checked against reservations")
    p.add_argument("--context", default="sprite", choices=["sprite", "portrait"])
    p.add_argument("--output-grid", help="write the composed head as a text grid")
    p.add_argument("--write-layer", help="write all four directions as rig layer <name>")
    p.add_argument("--rig-root", default="art/src/rig", help="rig root for --write-layer")
    p.add_argument("--preview", help="write a 1x/4x PNG preview")
    p.set_defaults(func=cmd_face_compose)

    p = sub.add_parser("face-sheet", help="labelled review sheets for the face kit")
    p.add_argument("--kit", required=True, help="face-kit directory (kit.json)")
    p.add_argument("--output", required=True, help="sheet PNG (a -carpet companion is written with --carpet)")
    p.add_argument("--skin", action="append", help="skin swap per column group (default: all four ramps)")
    p.add_argument("--carpet", action="append", help="carpet tile grid for the in-context companion sheet")
    p.add_argument("--carpet-face", action="append", help="faces to repeat on the carpets (default: all)")
    p.add_argument("--directions", default="brows", help="also write a directions sheet for this face (default: brows)")
    p.add_argument("--directions-output")
    p.set_defaults(func=cmd_face_sheet)

    p = sub.add_parser("refine", help="apply a refinement recipe to a grid")
    p.add_argument("source")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--recipe")
    g.add_argument("--ops", help="inline JSON list of ops")
    p.add_argument("--output")
    p.add_argument("--preview")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_refine)

    p = sub.add_parser("unzoom", help="restore the native grid of an upscaled image")
    p.add_argument("image")
    p.add_argument("--output-grid", required=True)
    p.add_argument("--scale", type=int)
    p.add_argument("--category")
    p.add_argument("--remove-background", action="store_true")
    p.add_argument("--tolerance", type=int, default=0)
    p.add_argument("--preview")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_unzoom)

    p = sub.add_parser("remove-bg", help="make the border-touching flat colour transparent")
    p.add_argument("image")
    p.add_argument("--output", required=True)
    p.add_argument("--tolerance", type=int, default=0)
    p.set_defaults(func=cmd_remove_bg)

    p = sub.add_parser("reduce", help="limit a grid to its N most-used colours")
    p.add_argument("source")
    p.add_argument("--max", type=int, required=True)
    p.add_argument("--keep", action="append")
    p.add_argument("--output", required=True)
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_reduce)

    p = sub.add_parser("lint", help="report isolated pixels, pinholes, doubled outlines")
    p.add_argument("source")
    p.add_argument("--outline", default="ink-1")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("fix", help="fix isolated pixels and pinholes")
    p.add_argument("source")
    p.add_argument("--output")
    p.add_argument("--preview")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_fix)

    p = sub.add_parser("autotile", help="build the 47-tile blob set from a 4x3 source")
    p.add_argument("source")
    p.add_argument("--tile", type=int, default=16)
    p.add_argument("--filler", help="tile drawn under empty cells in the sample map")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_autotile)

    p = sub.add_parser("seams", help="check a tile for grid lines and edge breaks")
    p.add_argument("source")
    p.add_argument("--preview")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_seams)

    p = sub.add_parser("nineslice", help="build a nine-slice panel config and previews")
    p.add_argument("source")
    p.add_argument("--slice", help="left,top,right,bottom")
    p.add_argument("--size", action="append", help="preview size WxH")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--frame-ms", type=int, default=500, help="animated frame duration in milliseconds")
    p.add_argument("--palette", **pal)
    p.set_defaults(func=cmd_nineslice)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except PixelCoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
