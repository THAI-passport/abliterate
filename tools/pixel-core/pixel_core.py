"""Deterministic shared tooling for All. Always. pixel assets.

The module intentionally has one runtime dependency: Pillow.  Everything else,
including the small TrueType writer, uses the Python standard library.  The
public functions are also used by ``pixel_tool.py`` so the four repository
skills enforce the same rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import json
import math
import re
import struct
import unicodedata
import colorsys
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - exercised only on an unprepared host
    Image = None
    ImageDraw = None


class PixelCoreError(ValueError):
    """An input cannot be parsed or built safely."""


def require_pillow() -> None:
    if Image is None:
        raise PixelCoreError(
            "Pillow is required for PNG rendering and image conversion; "
            "install the 'Pillow' Python package"
        )


def _parse_hex(value: str) -> tuple[int, int, int, int]:
    raw = value.strip().removeprefix("#")
    if len(raw) not in (6, 8) or not re.fullmatch(r"[0-9a-fA-F]+", raw):
        raise PixelCoreError(f"invalid colour {value!r}; expected #RRGGBB")
    rgba = tuple(int(raw[index : index + 2], 16) for index in range(0, len(raw), 2))
    if len(rgba) == 3:
        return rgba[0], rgba[1], rgba[2], 255
    if rgba[3] != 255:
        raise PixelCoreError(
            f"palette colour {value!r} is not opaque; transparency is separate from the palette"
        )
    return rgba  # type: ignore[return-value]


def _normalise_roles(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        parts = re.split(r"\s*[,|]\s*", value.strip())
        return tuple(part for part in parts if part)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    return (str(value).strip(),)


@dataclass(frozen=True)
class PaletteColor:
    name: str
    rgba: tuple[int, int, int, int]
    group: str = "ungrouped"
    roles: tuple[str, ...] = ()

    @property
    def hex(self) -> str:
        return "#" + "".join(f"{channel:02x}" for channel in self.rgba[:3])


@dataclass(frozen=True)
class Palette:
    name: str
    colors: tuple[PaletteColor, ...]
    source: Path | None = None
    ramps: dict[str, tuple[str, ...]] = field(default_factory=dict, compare=False)
    subsets: dict[str, tuple[str, ...]] = field(default_factory=dict, compare=False)

    @property
    def by_name(self) -> dict[str, PaletteColor]:
        return {color.name: color for color in self.colors}

    @property
    def opaque_rgbs(self) -> set[tuple[int, int, int]]:
        return {color.rgba[:3] for color in self.colors}

    def first_by_rgb(self) -> dict[tuple[int, int, int], PaletteColor]:
        result: dict[tuple[int, int, int], PaletteColor] = {}
        for color in self.colors:
            result.setdefault(color.rgba[:3], color)
        return result


def load_palette(path: str | Path) -> Palette:
    """Load the sole editable palette source.

    Canonical shape::

        {"name": "game", "colors": [
          {"name": "ink-1", "hex": "#12141a", "group": "ink",
           "role": ["outline", "text"]}
        ]}

    A mapping of colour names to hex values is accepted as a convenience for a
    temporary palette, but generated files should use the canonical shape.
    """

    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PixelCoreError(f"palette not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise PixelCoreError(
            f"{source}:{exc.lineno}:{exc.colno}: invalid palette JSON: {exc.msg}"
        ) from exc

    if isinstance(payload, list):
        name = source.stem
        raw_colors: Any = payload
    elif isinstance(payload, Mapping):
        name = str(payload.get("name") or source.stem)
        raw_colors = payload.get("colors")
        if raw_colors is None:
            raw_colors = {
                key: value
                for key, value in payload.items()
                if key not in {"name", "version", "description", "license", "author", "groups"}
            }
    else:
        raise PixelCoreError(f"{source}: palette JSON must be an object or list")

    entries: list[tuple[str, Any]] = []
    if isinstance(raw_colors, Mapping):
        entries = [(str(key), value) for key, value in raw_colors.items()]
    elif isinstance(raw_colors, Sequence) and not isinstance(raw_colors, (str, bytes, bytearray)):
        for index, value in enumerate(raw_colors):
            if isinstance(value, Mapping):
                entry_name = value.get("name")
                if not entry_name:
                    raise PixelCoreError(f"{source}: colors[{index}] is missing a name")
                entries.append((str(entry_name), value))
            elif isinstance(value, str):
                entries.append((f"color-{index + 1:02d}", value))
            else:
                raise PixelCoreError(f"{source}: colors[{index}] must be a string or object")
    else:
        raise PixelCoreError(f"{source}: 'colors' must be a list or object")

    colors: list[PaletteColor] = []
    seen_names: set[str] = set()
    for index, (entry_name, value) in enumerate(entries):
        clean_name = entry_name.strip()
        if not clean_name:
            raise PixelCoreError(f"{source}: colors[{index}] has an empty name")
        if clean_name in seen_names:
            raise PixelCoreError(f"{source}: duplicate palette colour name {clean_name!r}")
        seen_names.add(clean_name)
        if isinstance(value, str):
            hex_value = value
            group = "ungrouped"
            roles: tuple[str, ...] = ()
        elif isinstance(value, Mapping):
            hex_value = value.get("hex", value.get("value", value.get("color")))
            if not isinstance(hex_value, str):
                raise PixelCoreError(f"{source}: colour {clean_name!r} is missing a hex value")
            group = str(value.get("group") or "ungrouped")
            roles = _normalise_roles(value.get("roles", value.get("role")))
        else:
            raise PixelCoreError(f"{source}: colour {clean_name!r} must be a string or object")
        colors.append(PaletteColor(clean_name, _parse_hex(hex_value), group, roles))

    if not colors:
        raise PixelCoreError(f"{source}: palette has no colours")
    def named_sets(key: str) -> dict[str, tuple[str, ...]]:
        if not isinstance(payload, Mapping):
            return {}
        raw_sets = payload.get(key, {})
        if raw_sets is None:
            return {}
        if not isinstance(raw_sets, Mapping):
            raise PixelCoreError(f"{source}: {key!r} must be an object")
        result: dict[str, tuple[str, ...]] = {}
        for set_name, members in raw_sets.items():
            if not isinstance(members, Sequence) or isinstance(members, (str, bytes, bytearray)):
                raise PixelCoreError(f"{source}: {key}.{set_name} must be a list of colour names")
            result[str(set_name)] = tuple(str(member) for member in members)
        return result

    return Palette(
        name=name,
        colors=tuple(colors),
        source=source,
        ramps=named_sets("ramps"),
        subsets=named_sets("subsets"),
    )


@dataclass
class GridAsset:
    width: int
    height: int
    palette_name: str
    declared_frames: int
    origin: tuple[int, int] | None
    legend: dict[str, str]
    frames: list[list[str]]
    metadata: dict[str, str] = field(default_factory=dict)
    source: Path | None = None

    @property
    def category(self) -> str | None:
        value = self.metadata.get("category")
        return value.strip().lower() if value else None


@dataclass
class PngAsset:
    source: Path
    sidecar: Path
    has_sidecar: bool
    palette_name: str | None
    category: str | None
    origin: tuple[int, int] | None
    declared_frames: int
    frame_width: int
    frame_height: int
    sheet_width: int
    sheet_height: int
    metadata: dict[str, str] = field(default_factory=dict)


def _json_size(value: Any, *, label: str) -> tuple[int, int]:
    if isinstance(value, str):
        return parse_size(value, label=label)
    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and len(value) == 2
    ):
        try:
            width, height = int(value[0]), int(value[1])
        except (TypeError, ValueError) as exc:
            raise PixelCoreError(f"{label} must contain two integers") from exc
        if width <= 0 or height <= 0:
            raise PixelCoreError(f"{label} dimensions must be positive")
        return width, height
    raise PixelCoreError(f"{label} must be [WIDTH, HEIGHT] or 'WIDTHxHEIGHT'")


def _json_origin(value: Any) -> tuple[int, int]:
    if isinstance(value, str):
        return parse_origin(value)
    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and len(value) == 2
    ):
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError) as exc:
            raise PixelCoreError("origin must contain two integers") from exc
    raise PixelCoreError("origin must be [X, Y] or 'X,Y'")


def load_png_asset(path: str | Path, *, category: str | None = None) -> PngAsset:
    """Load an indexed-PNG source and its optional ``<stem>.json`` metadata."""

    require_pillow()
    source = Path(path)
    sidecar = source.with_suffix(".json")
    try:
        with Image.open(source) as opened:
            sheet_width, sheet_height = opened.size
    except FileNotFoundError as exc:
        raise PixelCoreError(f"PNG not found: {source}") from exc
    except Exception as exc:
        raise PixelCoreError(f"cannot read image {source}: {exc}") from exc

    payload: Mapping[str, Any] = {}
    if sidecar.is_file():
        try:
            loaded = json.loads(sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PixelCoreError(
                f"{sidecar}:{exc.lineno}:{exc.colno}: invalid PNG sidecar JSON: {exc.msg}"
            ) from exc
        if not isinstance(loaded, Mapping):
            raise PixelCoreError(f"{sidecar}: PNG sidecar must be a JSON object")
        payload = loaded

    try:
        frames = int(payload.get("frames", 1))
    except (TypeError, ValueError) as exc:
        raise PixelCoreError(f"{sidecar}: frames must be a positive integer") from exc
    if frames <= 0:
        raise PixelCoreError(f"{sidecar}: frames must be a positive integer")
    frame_value = payload.get("frameSize", payload.get("frame_size"))
    if frame_value is None:
        if sheet_width % frames:
            raise PixelCoreError(
                f"{sidecar}: PNG width {sheet_width} is not divisible by {frames} frames; "
                "set frameSize explicitly"
            )
        frame_width, frame_height = sheet_width // frames, sheet_height
    else:
        frame_width, frame_height = _json_size(frame_value, label="frameSize")
    origin_value = payload.get("origin")
    origin = _json_origin(origin_value) if origin_value is not None else None
    declared_category = category or payload.get("category")
    category_name = str(declared_category).strip().lower() if declared_category else None
    palette_value = payload.get("palette")
    palette_name = str(palette_value).strip() if palette_value else None
    reserved = {"palette", "category", "origin", "frames", "frameSize", "frame_size", "name"}
    metadata: dict[str, str] = {}
    for key, value in payload.items():
        if key in reserved:
            continue
        if isinstance(value, bool):
            metadata[str(key)] = "true" if value else "false"
        elif isinstance(value, (str, int, float)):
            metadata[str(key)] = str(value)
    return PngAsset(
        source=source,
        sidecar=sidecar,
        has_sidecar=sidecar.is_file(),
        palette_name=palette_name,
        category=category_name,
        origin=origin,
        declared_frames=frames,
        frame_width=frame_width,
        frame_height=frame_height,
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        metadata=metadata,
    )


_SIZE_RE = re.compile(r"^(\d+)\s*[xX×]\s*(\d+)$")
_ORIGIN_RE = re.compile(r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*$")
_FRAME_RE = re.compile(r"^(?:frame\s+\d+|grid)\s*:\s*$", re.IGNORECASE)
_HEADER_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")


def parse_size(value: str, *, label: str = "size") -> tuple[int, int]:
    match = _SIZE_RE.fullmatch(value.strip())
    if not match:
        raise PixelCoreError(f"invalid {label} {value!r}; expected WIDTHxHEIGHT")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0:
        raise PixelCoreError(f"invalid {label} {value!r}; dimensions must be positive")
    return width, height


def parse_origin(value: str) -> tuple[int, int]:
    match = _ORIGIN_RE.fullmatch(value)
    if not match:
        raise PixelCoreError(f"invalid origin {value!r}; expected X,Y")
    return int(match.group(1)), int(match.group(2))


def parse_grid_text(text: str, *, source: str | Path | None = None) -> GridAsset:
    source_path = Path(source) if source is not None else None
    source_label = str(source_path or "<grid>")
    headers: dict[str, str] = {}
    legend: dict[str, str] = {}
    frames: list[list[str]] = []
    current_frame: list[str] | None = None
    state = "header"

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.rstrip("\r")
        stripped = raw.strip()
        if state != "grid" and (not stripped or stripped.startswith("#")):
            continue

        if _FRAME_RE.fullmatch(stripped):
            current_frame = []
            frames.append(current_frame)
            state = "grid"
            continue

        if stripped.lower() == "legend:":
            state = "legend"
            continue

        if state == "grid":
            if stripped == "":
                continue
            assert current_frame is not None
            current_frame.append(raw)
            continue

        if state == "legend":
            # Indentation is cosmetic; a literal space is intentionally not a
            # legend symbol because it makes row widths invisible in reviews.
            match = re.match(r"^(.)\s*=\s*(.*?)\s*$", raw.lstrip())
            if not match or not match.group(2):
                raise PixelCoreError(
                    f"{source_label}:{line_number}: invalid legend entry; expected 'x = colour-name'"
                )
            symbol, color_name = match.group(1), match.group(2)
            if symbol in legend:
                raise PixelCoreError(
                    f"{source_label}:{line_number}: duplicate legend symbol {symbol!r}"
                )
            legend[symbol] = color_name
            continue

        match = _HEADER_RE.fullmatch(stripped)
        if not match:
            raise PixelCoreError(
                f"{source_label}:{line_number}: invalid header; expected 'name: value'"
            )
        key, value = match.group(1).lower(), match.group(2)
        if key in headers:
            raise PixelCoreError(f"{source_label}:{line_number}: duplicate header {key!r}")
        headers[key] = value

    missing = [key for key in ("size", "palette", "frames") if key not in headers]
    if missing:
        raise PixelCoreError(f"{source_label}: missing required header(s): {', '.join(missing)}")
    width, height = parse_size(headers["size"])
    try:
        declared_frames = int(headers["frames"])
    except ValueError as exc:
        raise PixelCoreError(f"{source_label}: frames must be a positive integer") from exc
    if declared_frames <= 0:
        raise PixelCoreError(f"{source_label}: frames must be a positive integer")
    origin = parse_origin(headers["origin"]) if "origin" in headers else None
    metadata = {
        key: value
        for key, value in headers.items()
        if key not in {"size", "palette", "frames", "origin"}
    }
    return GridAsset(
        width=width,
        height=height,
        palette_name=headers["palette"],
        declared_frames=declared_frames,
        origin=origin,
        legend=legend,
        frames=frames,
        metadata=metadata,
        source=source_path,
    )


def load_grid(path: str | Path) -> GridAsset:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PixelCoreError(f"grid not found: {source}") from exc
    return parse_grid_text(text, source=source)


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str
    source: str | None = None

    def __str__(self) -> str:
        location = f" {self.source}:" if self.source else ""
        return f"{self.level.upper()} [{self.code}]{location} {self.message}"


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, message: str, source: str | None = None) -> None:
        self.issues.append(Issue("error", code, message, source))

    def warning(self, code: str, message: str, source: str | None = None) -> None:
        self.issues.append(Issue("warning", code, message, source))

    def extend(self, other: "ValidationReport") -> None:
        self.issues.extend(other.issues)

    def format(self) -> str:
        return "\n".join(str(issue) for issue in self.issues)


CATEGORY_MAXIMUMS: dict[str, tuple[int, int]] = {
    "tile": (16, 16),
    "character": (16, 32),
    "portrait": (64, 64),
    "machine": (16, 32),
    "slot-machine": (16, 32),
    "blackjack-table": (48, 32),
    "roulette-table": (64, 32),
    "minigame": (480, 270),
    "exterior": (160, 96),
    "document": (480, 270),
    "icon": (16, 16),
    "inline-icon": (12, 12),
    "verdict-text-glyph": (6, 10),
}

CATEGORY_EXACT: dict[str, tuple[int, int]] = {
    "icon": (16, 16),
    "inline-icon": (12, 12),
    "verdict-text-glyph": (6, 10),
}

KNOWN_CATEGORIES = set(CATEGORY_MAXIMUMS) | {
    "prop",
    "sprite",
    "world",
    "ui",
    "ui-frame",
    "glyph",
    "tile-source",  # PixelTech autotile sources (pixel_tech.py autotile)
}

RESERVED_SEMANTICS = {"money", "ruin", "skin"}

_GRID_SYMBOLS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%&+=?!:;<>[]{}()^~"

WORLD_CATEGORIES = {
    "tile",
    "character",
    "prop",
    "machine",
    "slot-machine",
    "blackjack-table",
    "roulette-table",
    "exterior",
    "sprite",
    "world",
}


def _truthy(value: str | None) -> bool:
    return bool(value and value.strip().lower() in {"1", "true", "yes", "on"})


def _opaque_name(asset: GridAsset, symbol: str) -> str | None:
    if symbol == "." and symbol not in asset.legend:
        return None
    name = asset.legend.get(symbol)
    if name is None or name.strip().lower() in {"transparent", "none", "alpha"}:
        return None
    return name


def _color_semantics(color: PaletteColor) -> set[str]:
    labels = {color.group.lower(), *(role.lower() for role in color.roles)}
    meanings: set[str] = set()
    if any("money" in label or label == "solvent" for label in labels):
        meanings.add("money")
    if any(
        "ruin" in label or label in {"warning", "stamp"}
        for label in labels
    ):
        meanings.add("ruin")
    if any("skin" in label for label in labels):
        meanings.add("skin")
    return meanings


def palette_for_semantics(
    palette: Palette, allowed: Iterable[str] = ()
) -> Palette:
    """Return the conversion palette with undeclared meaning colors removed."""

    allowed_set = {value.strip().lower() for value in allowed if value.strip()}
    unknown = allowed_set - RESERVED_SEMANTICS
    if unknown:
        raise PixelCoreError(
            "unknown semantic meaning(s): " + ", ".join(sorted(unknown))
        )
    colors = tuple(
        color
        for color in palette.colors
        if _color_semantics(color).issubset(allowed_set)
    )
    if not colors:
        raise PixelCoreError("semantic filtering removed every palette color")
    return Palette(
        name=palette.name,
        colors=colors,
        source=palette.source,
    )


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for channel in rgb:
        normal = channel / 255.0
        values.append(normal / 12.92 if normal <= 0.04045 else ((normal + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def _contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    light_a, light_b = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(light_a, light_b), min(light_a, light_b)
    return (lighter + 0.05) / (darker + 0.05)


def validate_palette(palette: Palette) -> ValidationReport:
    report = ValidationReport()
    source = str(palette.source) if palette.source else None
    if not 32 <= len(palette.colors) <= 64:
        report.warning(
            "palette-size",
            f"palette has {len(palette.colors)} colours; the art spec proposes 32-64",
            source,
        )
    for color in palette.colors:
        if color.rgba[:3] in {(0, 0, 0), (255, 255, 255)}:
            report.warning(
                "palette-extreme",
                f"{color.name!r} is pure {'black' if color.rgba[0] == 0 else 'white'}; "
                "the art spec calls for near-black and near-white",
                source,
            )
    by_rgb: dict[tuple[int, int, int], list[str]] = {}
    for color in palette.colors:
        by_rgb.setdefault(color.rgba[:3], []).append(color.name)
    for rgb, names in by_rgb.items():
        if len(names) > 1:
            report.warning(
                "palette-duplicate",
                f"{', '.join(repr(name) for name in names)} share "
                f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                source,
            )

    luminances = [_relative_luminance(color.rgba[:3]) for color in palette.colors]
    if min(luminances) > 0.04:
        report.warning("palette-near-black", "palette has no near-black for outlines and text", source)
    if max(luminances) < 0.80:
        report.warning("palette-near-white", "palette has no near-white", source)

    groups: dict[str, list[PaletteColor]] = {}
    for color in palette.colors:
        groups.setdefault(color.group, []).append(color)
    semantic_groups: dict[str, list[PaletteColor]] = {"skin": [], "money": [], "ruin": []}
    skin_ramps: set[str] = {
        ramp_name for ramp_name in palette.ramps if "skin" in ramp_name.lower()
    }
    for color in palette.colors:
        labels = {color.group.lower(), *(role.lower() for role in color.roles)}
        if any("skin" in label for label in labels):
            semantic_groups["skin"].append(color)
            skin_ramps.add(color.group)
        if any(label in {"money", "solvent"} or "money" in label for label in labels):
            semantic_groups["money"].append(color)
        if any(label in {"ruin", "warning", "stamp"} or "ruin" in label for label in labels):
            semantic_groups["ruin"].append(color)
    if len(skin_ramps) < 4:
        report.warning(
            "palette-skin-ramps",
            f"palette metadata identifies {len(skin_ramps)} skin ramp(s); at least 4 are required",
            source,
        )
    for meaning in ("money", "ruin"):
        if len(semantic_groups[meaning]) < 3:
            report.warning(
                f"palette-{meaning}-ramp",
                f"palette metadata identifies {len(semantic_groups[meaning])} {meaning} colour(s); "
                "a 3-5 step meaning ramp is required",
                source,
            )
    if semantic_groups["money"] and semantic_groups["ruin"]:
        money_lightness = sum(
            _relative_luminance(color.rgba[:3]) for color in semantic_groups["money"]
        ) / len(semantic_groups["money"])
        ruin_lightness = sum(
            _relative_luminance(color.rgba[:3]) for color in semantic_groups["ruin"]
        ) / len(semantic_groups["ruin"])
        if abs(money_lightness - ruin_lightness) < 0.10:
            report.warning(
                "palette-meaning-lightness",
                "money and ruin ramps have similar average lightness; they must differ in "
                "lightness as well as hue",
                source,
            )

    known_names = palette.by_name
    for kind, sets in (("ramp", palette.ramps), ("subset", palette.subsets)):
        for set_name, members in sets.items():
            unknown = [member for member in members if member not in known_names]
            if unknown:
                report.error(
                    f"palette-{kind}-colour",
                    f"{kind} {set_name!r} references unknown colour(s): {', '.join(unknown)}",
                    source,
                )
            if kind == "ramp" and not 3 <= len(members) <= 5:
                report.warning(
                    "palette-ramp-length",
                    f"ramp {set_name!r} has {len(members)} colours; material ramps should have 3-5",
                    source,
                )
    for required_subset in ("salon", "floor"):
        if required_subset not in {name.lower() for name in palette.subsets}:
            report.warning(
                "palette-mood-subset",
                f"palette has no named {required_subset!r} subset",
                source,
            )

    if palette.ramps:
        ramp_items = [
            (ramp_name, [known_names[name] for name in members if name in known_names])
            for ramp_name, members in palette.ramps.items()
        ]
    else:
        ramp_items = list(groups.items())
    for group_name, group_colors in ramp_items:
        if len(group_colors) < 3 or group_name == "ungrouped":
            continue
        hls = [
            colorsys.rgb_to_hls(
                color.rgba[0] / 255.0,
                color.rgba[1] / 255.0,
                color.rgba[2] / 255.0,
            )
            for color in group_colors
        ]
        saturated_hues = [hue for hue, _, saturation in hls if saturation >= 0.12]
        if len(saturated_hues) >= 2:
            ordered = sorted(saturated_hues)
            gaps = [
                ordered[index + 1] - ordered[index] for index in range(len(ordered) - 1)
            ] + [ordered[0] + 1.0 - ordered[-1]]
            hue_span = 1.0 - max(gaps)
            if hue_span < (4.0 / 360.0):
                report.warning(
                    "palette-hue-shift",
                    f"ramp {group_name!r} has no visible hue shift between tones",
                    source,
                )
    return report


def validate_grid_asset(
    asset: GridAsset,
    palette: Palette,
    *,
    category: str | None = None,
    require_category: bool = False,
) -> ValidationReport:
    report = ValidationReport()
    source = str(asset.source) if asset.source else "<grid>"
    category = (category or asset.category or "").lower() or None
    if require_category and category is None:
        report.error(
            "missing-category",
            "build inputs need a category so dimensions and world-origin rules can be enforced",
            source,
        )
    elif category is not None and category not in KNOWN_CATEGORIES:
        report.error(
            "unknown-category",
            f"unknown asset category {category!r}; use a category defined by the pixel-art spec",
            source,
        )
    if asset.palette_name != palette.name:
        report.error(
            "palette-name",
            f"grid names palette {asset.palette_name!r}, but loaded palette is {palette.name!r}",
            source,
        )
    if len(asset.frames) != asset.declared_frames:
        report.error(
            "frame-count",
            f"header declares {asset.declared_frames} frame(s), found {len(asset.frames)}",
            source,
        )
    if not asset.frames:
        report.error("missing-grid", "no grid/frame block was found", source)

    palette_names = palette.by_name
    for symbol, color_name in asset.legend.items():
        if symbol == "." and color_name.strip().lower() not in {"transparent", "none", "alpha"}:
            report.error("dot-not-transparent", "'.' is reserved for transparency", source)
        if color_name.strip().lower() not in {"transparent", "none", "alpha"} and color_name not in palette_names:
            report.error(
                "unknown-colour",
                f"legend symbol {symbol!r} names off-palette colour {color_name!r}",
                source,
            )

    used_symbols: set[str] = set()
    for frame_index, frame in enumerate(asset.frames, start=1):
        if len(frame) != asset.height:
            report.error(
                "grid-height",
                f"frame {frame_index} has {len(frame)} row(s), expected {asset.height}",
                source,
            )
        for row_index, row in enumerate(frame, start=1):
            if len(row) != asset.width:
                report.error(
                    "grid-width",
                    f"frame {frame_index}, row {row_index} has width {len(row)}, expected {asset.width}",
                    source,
                )
            used_symbols.update(row)
    for symbol in sorted(used_symbols):
        if symbol != "." and symbol not in asset.legend:
            report.error("undefined-symbol", f"grid uses undefined legend symbol {symbol!r}", source)

    declared_semantics = {
        value
        for value in re.split(r"[\s,|]+", asset.metadata.get("semantic", "").lower())
        if value
    }
    unknown_semantics = declared_semantics - RESERVED_SEMANTICS
    if unknown_semantics:
        report.error(
            "unknown-semantic",
            "unknown semantic meaning(s): " + ", ".join(sorted(unknown_semantics)),
            source,
        )
    used_color_names = {
        asset.legend[symbol]
        for symbol in used_symbols
        if symbol in asset.legend
        and asset.legend[symbol].strip().lower() not in {"transparent", "none", "alpha"}
        and asset.legend[symbol] in palette_names
    }
    for color_name in sorted(used_color_names):
        undeclared = _color_semantics(palette_names[color_name]) - declared_semantics
        if undeclared:
            report.error(
                "reserved-semantic",
                f"palette colour {color_name!r} is reserved for "
                f"{', '.join(sorted(undeclared))}; declare semantic: "
                f"{','.join(sorted(undeclared))} only when the asset has that meaning",
                source,
            )

    placed = _truthy(asset.metadata.get("placed")) or category in WORLD_CATEGORIES
    if placed and asset.origin is None:
        report.error(
            "missing-origin",
            f"{category or 'world'} asset is placed in the world and needs an origin",
            source,
        )
    if asset.origin is not None:
        x, y = asset.origin
        if not (0 <= x < asset.width and 0 <= y < asset.height):
            report.error(
                "origin-bounds",
                f"origin {x},{y} lies outside {asset.width}x{asset.height}",
                source,
            )

    exact = CATEGORY_EXACT.get(category or "")
    if exact and (asset.width, asset.height) != exact:
        report.error(
            "category-dimensions",
            f"{category} assets must be exactly {exact[0]}x{exact[1]}; "
            f"found {asset.width}x{asset.height}",
            source,
        )
    maximum = CATEGORY_MAXIMUMS.get(category or "")
    if "max-size" in asset.metadata:
        report.error(
            "max-size-override",
            "max-size cannot override the canonical category limit; use a recorded exception instead",
            source,
        )
    if not exact and maximum and (asset.width > maximum[0] or asset.height > maximum[1]):
        exception = asset.metadata.get("exception", "").strip()
        if not exception:
            report.error(
                "category-maximum",
                f"{asset.width}x{asset.height} exceeds {category} maximum "
                f"{maximum[0]}x{maximum[1]}; add a recorded exception only when approved",
                source,
            )

    # Isolated opaque pixels: review rather than reject because eyes and glints can be intentional.
    for frame_index, frame in enumerate(asset.frames, start=1):
        isolated: list[tuple[int, int]] = []
        for y in range(min(asset.height, len(frame))):
            row = frame[y]
            for x in range(min(asset.width, len(row))):
                if _opaque_name(asset, row[x]) is None:
                    continue
                neighbours = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= ny < len(frame) and 0 <= nx < len(frame[ny]):
                            neighbours.append(_opaque_name(asset, frame[ny][nx]))
                if not any(name is not None for name in neighbours):
                    isolated.append((x, y))
        if isolated:
            first = isolated[0]
            report.warning(
                "isolated-pixel",
                f"frame {frame_index} has {len(isolated)} isolated opaque pixel(s); "
                f"first at {first[0]},{first[1]}",
                source,
            )

    outline_names = {
        color.name
        for color in palette.colors
        if "outline" in color.roles or "outline" in color.name.lower()
    }
    explicit_outline = asset.metadata.get("outline")
    if explicit_outline:
        outline_names.update(part.strip() for part in explicit_outline.split(",") if part.strip())
    if category in {"character", "prop", "machine", "slot-machine"} and outline_names:
        for frame_index, frame in enumerate(asset.frames, start=1):
            gaps: list[tuple[int, int]] = []
            for y in range(min(asset.height, len(frame))):
                row = frame[y]
                for x in range(min(asset.width, len(row))):
                    color_name = _opaque_name(asset, row[x])
                    if color_name is None or color_name in outline_names:
                        continue
                    exposed = False
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = x + dx, y + dy
                        if not (0 <= ny < len(frame) and 0 <= nx < len(frame[ny])):
                            exposed = True
                            break
                        if _opaque_name(asset, frame[ny][nx]) is None:
                            exposed = True
                            break
                    if exposed:
                        gaps.append((x, y))
            if gaps:
                report.warning(
                    "outline-gap",
                    f"frame {frame_index} has {len(gaps)} exposed non-outline edge pixel(s); "
                    f"first at {gaps[0][0]},{gaps[0][1]}",
                    source,
                )

    background_name = asset.metadata.get("background")
    if background_name:
        background = palette_names.get(background_name)
        if background is None:
            report.error(
                "unknown-background",
                f"contrast background {background_name!r} is not in the palette",
                source,
            )
        else:
            try:
                minimum = float(asset.metadata.get("min-contrast", "3.0"))
            except ValueError:
                report.error("bad-contrast", "min-contrast must be a number", source)
            else:
                used_names = {
                    _opaque_name(asset, symbol)
                    for symbol in used_symbols
                    if _opaque_name(asset, symbol) is not None
                }
                for used_name in sorted(used_names):
                    assert used_name is not None
                    foreground = palette_names.get(used_name)
                    if foreground and foreground.name != background.name:
                        ratio = _contrast_ratio(foreground.rgba[:3], background.rgba[:3])
                        if ratio < minimum:
                            report.warning(
                                "low-contrast",
                                f"{foreground.name!r} against {background.name!r} has "
                                f"{ratio:.2f}:1 contrast, below {minimum:.2f}:1",
                                source,
                            )

    if _truthy(asset.metadata.get("mirrored")):
        for frame_index, frame in enumerate(asset.frames, start=1):
            asymmetric = any(row != row[::-1] for row in frame)
            if asymmetric:
                report.warning(
                    "mirrored-asymmetry",
                    f"frame {frame_index} is marked mirrored but has asymmetric details",
                    source,
                )
    return report


def _validate_png_pixels(path: Path, palette: Palette) -> tuple[ValidationReport, "Image.Image | None"]:
    require_pillow()
    report = ValidationReport()
    try:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
    except FileNotFoundError:
        report.error("missing-file", "PNG was not found", str(path))
        return report, None
    except Exception as exc:
        report.error("invalid-image", f"cannot read image: {exc}", str(path))
        return report, None
    partial: list[tuple[int, int, int]] = []
    off_palette: list[tuple[int, int, tuple[int, int, int]]] = []
    allowed = palette.opaque_rgbs
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = image.getpixel((x, y))
            if alpha not in (0, 255):
                partial.append((x, y, alpha))
            elif alpha == 255 and (red, green, blue) not in allowed:
                off_palette.append((x, y, (red, green, blue)))
    if partial:
        x, y, alpha = partial[0]
        report.error(
            "partial-alpha",
            f"{len(partial)} partially transparent pixel(s); first at {x},{y} has alpha {alpha}",
            str(path),
        )
    if off_palette:
        x, y, rgb = off_palette[0]
        report.error(
            "off-palette",
            f"{len(off_palette)} opaque off-palette pixel(s); first at {x},{y} is "
            f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
            str(path),
        )
    return report, image


def png_frames(asset: PngAsset) -> list["Image.Image"]:
    require_pillow()
    with Image.open(asset.source) as opened:
        sheet = opened.convert("RGBA")
    return [
        sheet.crop(
            (
                index * asset.frame_width,
                0,
                (index + 1) * asset.frame_width,
                asset.frame_height,
            )
        )
        for index in range(asset.declared_frames)
    ]


def _png_grid_asset(
    asset: PngAsset, palette: Palette, frames: Sequence["Image.Image"]
) -> GridAsset:
    by_rgb = palette.first_by_rgb()
    used_names: set[str] = set()
    name_frames: list[list[list[str | None]]] = []
    for image in frames:
        name_rows: list[list[str | None]] = []
        for y in range(image.height):
            row: list[str | None] = []
            for x in range(image.width):
                red, green, blue, alpha = image.getpixel((x, y))
                if alpha == 0:
                    row.append(None)
                else:
                    color = by_rgb[(red, green, blue)]
                    row.append(color.name)
                    used_names.add(color.name)
            name_rows.append(row)
        name_frames.append(name_rows)
    ordered_names = [color.name for color in palette.colors if color.name in used_names]
    if len(ordered_names) > len(_GRID_SYMBOLS):
        raise PixelCoreError("PNG uses too many colours for shared grid validation")
    symbol_by_name = {
        name: _GRID_SYMBOLS[index] for index, name in enumerate(ordered_names)
    }
    legend = {".": "transparent"}
    legend.update({symbol_by_name[name]: name for name in ordered_names})
    text_frames = [
        [
            "".join("." if name is None else symbol_by_name[name] for name in row)
            for row in name_rows
        ]
        for name_rows in name_frames
    ]
    metadata = dict(asset.metadata)
    if asset.category:
        metadata["category"] = asset.category
    return GridAsset(
        width=asset.frame_width,
        height=asset.frame_height,
        palette_name=asset.palette_name or palette.name,
        declared_frames=asset.declared_frames,
        origin=asset.origin,
        legend=legend,
        frames=text_frames,
        metadata=metadata,
        source=asset.source,
    )


def validate_png_asset(
    asset: PngAsset,
    palette: Palette,
    *,
    require_sidecar: bool = False,
    require_category: bool = False,
) -> ValidationReport:
    report, image = _validate_png_pixels(asset.source, palette)
    if require_sidecar and not asset.has_sidecar:
        report.error(
            "missing-png-sidecar",
            f"indexed PNG build inputs need metadata at {asset.sidecar.name}",
            str(asset.source),
        )
    if asset.has_sidecar and not asset.palette_name:
        report.error(
            "missing-palette-metadata",
            "PNG sidecar needs a palette name",
            str(asset.sidecar),
        )
    if asset.palette_name and asset.palette_name != palette.name:
        report.error(
            "palette-name",
            f"PNG sidecar names palette {asset.palette_name!r}, but loaded palette is {palette.name!r}",
            str(asset.sidecar),
        )
    if (
        asset.sheet_width != asset.frame_width * asset.declared_frames
        or asset.sheet_height != asset.frame_height
    ):
        report.error(
            "png-frame-layout",
            f"sheet is {asset.sheet_width}x{asset.sheet_height}, but {asset.declared_frames} "
            f"horizontal {asset.frame_width}x{asset.frame_height} frame(s) require "
            f"{asset.frame_width * asset.declared_frames}x{asset.frame_height}",
            str(asset.source),
        )
    if image is not None and report.ok:
        frames = png_frames(asset)
        report.extend(
            validate_grid_asset(
                _png_grid_asset(asset, palette, frames),
                palette,
                require_category=require_category,
            )
        )
    return report


def validate_png(
    path: str | Path,
    palette: Palette,
    *,
    category: str | None = None,
    require_sidecar: bool = False,
    require_category: bool = False,
) -> ValidationReport:
    try:
        asset = load_png_asset(path, category=category)
    except PixelCoreError as exc:
        report = ValidationReport()
        report.error("png-metadata", str(exc), str(path))
        return report
    return validate_png_asset(
        asset,
        palette,
        require_sidecar=require_sidecar,
        require_category=require_category,
    )


def _raise_for_report(report: ValidationReport) -> None:
    if report.errors:
        raise PixelCoreError(report.format())


def render_frames(
    asset: GridAsset, palette: Palette, *, scale: int = 1
) -> list["Image.Image"]:
    require_pillow()
    if scale <= 0:
        raise PixelCoreError("render scale must be a positive integer")
    report = validate_grid_asset(asset, palette)
    _raise_for_report(report)
    palette_names = palette.by_name
    frame_images: list[Image.Image] = []
    for frame in asset.frames:
        image = Image.new("RGBA", (asset.width, asset.height), (0, 0, 0, 0))
        pixels = image.load()
        for y, row in enumerate(frame):
            for x, symbol in enumerate(row):
                name = _opaque_name(asset, symbol)
                if name is not None:
                    pixels[x, y] = palette_names[name].rgba
        frame_images.append(image)
    if scale != 1:
        frame_images = [
            image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
            for image in frame_images
        ]
    return frame_images


def render_asset(asset: GridAsset, palette: Palette, *, scale: int = 1) -> "Image.Image":
    frame_images = render_frames(asset, palette, scale=scale)
    strip = Image.new(
        "RGBA",
        (frame_images[0].width * len(frame_images), frame_images[0].height),
        (0, 0, 0, 0),
    )
    for index, image in enumerate(frame_images):
        strip.alpha_composite(image, (index * image.width, 0))
    return strip


def save_render(
    asset: GridAsset,
    palette: Palette,
    output: str | Path,
    *,
    scale: int = 1,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_asset(asset, palette, scale=scale).save(output_path, format="PNG", optimize=False)
    return output_path


def write_animation_preview(
    asset: GridAsset,
    palette: Palette,
    output: str | Path,
    *,
    scale: int = 4,
    duration_ms: int | None = None,
) -> Path:
    """Write a nearest-neighbour GIF for a multi-frame grid."""

    require_pillow()
    if len(asset.frames) < 2:
        raise PixelCoreError("animated preview needs at least two frames")
    if duration_ms is None:
        try:
            hold = int(asset.metadata.get("frame-hold", "8"))
        except ValueError as exc:
            raise PixelCoreError("frame-hold must be an integer number of 60 fps frames") from exc
        if hold <= 0:
            raise PixelCoreError("frame-hold must be positive")
        duration_ms = max(1, round(hold * 1000 / 60))
    if duration_ms <= 0:
        raise PixelCoreError("animation duration must be positive")
    frames = [_flatten_on_checker(frame) for frame in render_frames(asset, palette, scale=scale)]
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output_path


def _checkerboard(width: int, height: int, *, cell: int = 4) -> "Image.Image":
    require_pillow()
    image = Image.new("RGBA", (width, height), (202, 205, 211, 255))
    draw = ImageDraw.Draw(image)
    alternate = (235, 237, 241, 255)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2 == 0:
                draw.rectangle((x, y, min(width - 1, x + cell - 1), min(height - 1, y + cell - 1)), fill=alternate)
    return image


def _flatten_on_checker(image: "Image.Image") -> "Image.Image":
    background = _checkerboard(image.width, image.height)
    background.alpha_composite(image.convert("RGBA"))
    return background


def write_preview(
    entries: Sequence[tuple[str, "Image.Image"]],
    output: str | Path,
    *,
    scales: Sequence[int] = (1, 4),
) -> Path:
    """Write a labelled contact sheet showing every input at each integer scale."""

    require_pillow()
    if not entries:
        raise PixelCoreError("preview needs at least one input")
    if not scales or any(scale <= 0 for scale in scales):
        raise PixelCoreError("preview scales must be positive integers")
    margin, gap, label_height = 10, 12, 26
    row_heights: list[int] = []
    row_widths: list[int] = []
    for _, image in entries:
        row_heights.append(label_height + max(image.height * scale for scale in scales))
        row_widths.append(sum(image.width * scale for scale in scales) + gap * (len(scales) - 1))
    canvas = Image.new(
        "RGBA",
        (max(row_widths) + margin * 2, sum(row_heights) + gap * (len(entries) - 1) + margin * 2),
        (45, 48, 56, 255),
    )
    draw = ImageDraw.Draw(canvas)
    y = margin
    for (name, image), row_height in zip(entries, row_heights):
        draw.text((margin, y), name, fill=(245, 245, 240, 255))
        x = margin
        image_y = y + label_height
        for scale in scales:
            draw.text((x, y + 12), f"{scale}x", fill=(205, 208, 216, 255))
            scaled = image.resize(
                (image.width * scale, image.height * scale), Image.Resampling.NEAREST
            )
            flattened = _flatten_on_checker(scaled)
            canvas.alpha_composite(flattened, (x, image_y))
            x += scaled.width + gap
        y += row_height + gap
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=False)
    return output_path


def load_preview_image(path: str | Path, palette: Palette) -> tuple["Image.Image", ValidationReport]:
    require_pillow()
    source = Path(path)
    if source.suffix.lower() in {".txt", ".grid", ".px"}:
        asset = load_grid(source)
        report = validate_grid_asset(asset, palette)
        if report.ok:
            return render_asset(asset, palette), report
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), report
    report = validate_png(source, palette)
    if report.ok:
        with Image.open(source) as opened:
            return opened.convert("RGBA"), report
    return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), report


def export_palette(
    palette: Palette,
    out_dir: str | Path,
    *,
    basename: str | None = None,
) -> dict[str, Path]:
    require_pillow()
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    base = basename or (palette.source.stem if palette.source else palette.name)
    hex_path = destination / f"{base}.hex"
    gpl_path = destination / f"{base}.gpl"
    swatch_path = destination / "swatch.png"
    hex_path.write_text("".join(f"{color.hex}\n" for color in palette.colors), encoding="utf-8")
    gpl_lines = ["GIMP Palette", f"Name: {palette.name}", "Columns: 8", "#"]
    for color in palette.colors:
        red, green, blue = color.rgba[:3]
        gpl_lines.append(f"{red:3d} {green:3d} {blue:3d}\t{color.name}")
    gpl_path.write_text("\n".join(gpl_lines) + "\n", encoding="utf-8")
    columns = min(8, len(palette.colors))
    rows = math.ceil(len(palette.colors) / columns)
    cell = 16
    swatch = Image.new("RGBA", (columns * cell, rows * cell), (0, 0, 0, 0))
    draw = ImageDraw.Draw(swatch)
    for index, color in enumerate(palette.colors):
        x, y = (index % columns) * cell, (index // columns) * cell
        draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=color.rgba)
    swatch.save(swatch_path, format="PNG", optimize=False)
    return {"hex": hex_path, "gpl": gpl_path, "swatch": swatch_path}


def _nearest_color(rgb: tuple[int, int, int], palette: Palette) -> PaletteColor:
    red, green, blue = rgb
    _, color = min(
        enumerate(palette.colors),
        key=lambda item: (
            3 * (red - item[1].rgba[0]) ** 2
            + 4 * (green - item[1].rgba[1]) ** 2
            + 2 * (blue - item[1].rgba[2]) ** 2,
            item[0],
        ),
    )
    return color


_BAYER_4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def resize_reference(
    image: "Image.Image",
    size: tuple[int, int],
    *,
    crop: str = "cover",
) -> "Image.Image":
    require_pillow()
    target_width, target_height = size
    image = image.convert("RGBA")
    if crop == "cover":
        source_ratio = image.width / image.height
        target_ratio = target_width / target_height
        if source_ratio > target_ratio:
            new_width = max(1, round(image.height * target_ratio))
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        elif source_ratio < target_ratio:
            new_height = max(1, round(image.width / target_ratio))
            top = (image.height - new_height) // 2
            image = image.crop((0, top, image.width, top + new_height))
        return image.resize(size, Image.Resampling.BOX)
    if crop == "fit":
        ratio = min(target_width / image.width, target_height / image.height)
        fitted_size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
        fitted = image.resize(fitted_size, Image.Resampling.BOX)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        canvas.alpha_composite(
            fitted, ((target_width - fitted.width) // 2, (target_height - fitted.height) // 2)
        )
        return canvas
    raise PixelCoreError(f"unknown crop mode {crop!r}; expected 'cover' or 'fit'")


def map_image_to_palette(
    image: "Image.Image",
    palette: Palette,
    *,
    dither: bool = False,
    dither_strength: int = 24,
    alpha_threshold: int = 128,
) -> tuple["Image.Image", list[list[str | None]]]:
    require_pillow()
    if not 0 <= alpha_threshold <= 255:
        raise PixelCoreError("alpha threshold must be between 0 and 255")
    if dither_strength < 0:
        raise PixelCoreError("dither strength cannot be negative")
    source = image.convert("RGBA")
    mapped = Image.new("RGBA", source.size, (0, 0, 0, 0))
    grid: list[list[str | None]] = []
    for y in range(source.height):
        row: list[str | None] = []
        for x in range(source.width):
            red, green, blue, alpha = source.getpixel((x, y))
            if alpha < alpha_threshold:
                row.append(None)
                continue
            if dither:
                adjustment = round(((_BAYER_4[y % 4][x % 4] + 0.5) / 16 - 0.5) * dither_strength)
                red = min(255, max(0, red + adjustment))
                green = min(255, max(0, green + adjustment))
                blue = min(255, max(0, blue + adjustment))
            color = _nearest_color((red, green, blue), palette)
            mapped.putpixel((x, y), color.rgba)
            row.append(color.name)
        grid.append(row)
    return mapped, grid


def format_grid(
    grid: Sequence[Sequence[str | None]],
    palette: Palette,
    *,
    category: str | None = None,
    origin: tuple[int, int] | None = None,
    extra_metadata: Mapping[str, str] | None = None,
) -> str:
    if not grid or not grid[0]:
        raise PixelCoreError("cannot format an empty grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise PixelCoreError("cannot format grid with uneven row widths")
    used = {name for row in grid for name in row if name is not None}
    ordered_names = [color.name for color in palette.colors if color.name in used]
    if len(ordered_names) > len(_GRID_SYMBOLS):
        raise PixelCoreError(
            f"grid uses {len(ordered_names)} colours, but the text legend supports "
            f"{len(_GRID_SYMBOLS)} symbols"
        )
    symbols = {name: _GRID_SYMBOLS[index] for index, name in enumerate(ordered_names)}
    lines = [
        f"size: {width}x{len(grid)}",
        f"palette: {palette.name}",
        "frames: 1",
    ]
    if origin is not None:
        lines.append(f"origin: {origin[0]},{origin[1]}")
    if category:
        lines.append(f"category: {category}")
    if extra_metadata:
        for key, value in extra_metadata.items():
            lines.append(f"{key}: {value}")
    lines.extend(["legend:", "  . = transparent"])
    for name in ordered_names:
        lines.append(f"  {symbols[name]} = {name}")
    lines.append("grid:")
    for row in grid:
        lines.append("".join("." if name is None else symbols[name] for name in row))
    return "\n".join(lines) + "\n"


def convert_image(
    input_path: str | Path,
    palette: Palette,
    size: tuple[int, int],
    *,
    crop: str = "cover",
    dither: bool = False,
    dither_strength: int = 24,
    alpha_threshold: int = 128,
) -> tuple["Image.Image", "Image.Image", list[list[str | None]]]:
    require_pillow()
    source_path = Path(input_path)
    try:
        with Image.open(source_path) as opened:
            resized = resize_reference(opened, size, crop=crop)
    except FileNotFoundError as exc:
        raise PixelCoreError(f"reference image not found: {source_path}") from exc
    mapped, grid = map_image_to_palette(
        resized,
        palette,
        dither=dither,
        dither_strength=dither_strength,
        alpha_threshold=alpha_threshold,
    )
    return resized, mapped, grid


def write_conversion_preview(
    original: "Image.Image", mapped: "Image.Image", output: str | Path
) -> Path:
    """Write reference and mapped results beside one another at 1x and 4x."""

    require_pillow()
    margin, gap, heading, row_gap = 10, 12, 26, 12
    scales = (1, 4)
    widths = [original.width * scale + gap + mapped.width * scale for scale in scales]
    heights = [heading + max(original.height, mapped.height) * scale for scale in scales]
    canvas = Image.new(
        "RGBA",
        (max(widths) + margin * 2, sum(heights) + row_gap + margin * 2),
        (45, 48, 56, 255),
    )
    draw = ImageDraw.Draw(canvas)
    y = margin
    for scale, row_height in zip(scales, heights):
        draw.text((margin, y), f"{scale}x  reference | palette-mapped", fill=(245, 245, 240, 255))
        image_y = y + heading
        left = original.resize(
            (original.width * scale, original.height * scale), Image.Resampling.NEAREST
        )
        right = mapped.resize(
            (mapped.width * scale, mapped.height * scale), Image.Resampling.NEAREST
        )
        canvas.alpha_composite(_flatten_on_checker(left), (margin, image_y))
        canvas.alpha_composite(_flatten_on_checker(right), (margin + left.width + gap, image_y))
        y += row_height + row_gap
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=False)
    return output_path


def _pack_images(
    entries: Sequence[tuple[str, "Image.Image"]],
    *,
    columns: int = 8,
    padding: int = 1,
) -> tuple["Image.Image", dict[str, dict[str, Any]]]:
    require_pillow()
    if not entries:
        raise PixelCoreError("atlas needs at least one image")
    if columns <= 0:
        raise PixelCoreError("atlas columns must be positive")
    cell_width = max(image.width for _, image in entries)
    cell_height = max(image.height for _, image in entries)
    columns = min(columns, len(entries))
    rows = math.ceil(len(entries) / columns)
    atlas = Image.new(
        "RGBA",
        (columns * (cell_width + padding) - padding, rows * (cell_height + padding) - padding),
        (0, 0, 0, 0),
    )
    frames: dict[str, dict[str, Any]] = {}
    for index, (name, image) in enumerate(entries):
        x = (index % columns) * (cell_width + padding)
        y = (index // columns) * (cell_height + padding)
        atlas.alpha_composite(image.convert("RGBA"), (x, y))
        frames[name] = {
            "frame": {"x": x, "y": y, "w": image.width, "h": image.height},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": image.width, "h": image.height},
            "sourceSize": {"w": image.width, "h": image.height},
        }
    return atlas, frames


@dataclass(frozen=True)
class AtlasEntry:
    name: str
    image: "Image.Image"
    origin: tuple[int, int] | None
    category: str
    source: Path


def load_asset_entries(
    path: str | Path,
    palette: Palette,
    *,
    name: str | None = None,
    category: str | None = None,
    require_png_sidecar: bool = True,
) -> tuple[list[AtlasEntry], ValidationReport]:
    source = Path(path)
    base_name = name or source.stem
    report = ValidationReport()
    entries: list[AtlasEntry] = []
    if source.suffix.lower() in {".txt", ".grid", ".px"}:
        asset = load_grid(source)
        resolved_category = (category or asset.category or "").lower()
        item_report = validate_grid_asset(
            asset,
            palette,
            category=resolved_category or None,
            require_category=True,
        )
        report.extend(item_report)
        if item_report.ok:
            images = render_frames(asset, palette)
            for index, image in enumerate(images):
                frame_name = base_name if len(images) == 1 else f"{base_name}/{index}"
                entries.append(
                    AtlasEntry(frame_name, image, asset.origin, resolved_category, source)
                )
        return entries, report
    if source.suffix.lower() == ".png":
        asset = load_png_asset(source, category=category)
        item_report = validate_png_asset(
            asset,
            palette,
            require_sidecar=require_png_sidecar,
            require_category=True,
        )
        report.extend(item_report)
        if item_report.ok:
            images = png_frames(asset)
            for index, image in enumerate(images):
                frame_name = base_name if len(images) == 1 else f"{base_name}/{index}"
                entries.append(
                    AtlasEntry(
                        frame_name,
                        image,
                        asset.origin,
                        asset.category or "",
                        source,
                    )
                )
        return entries, report
    report.error(
        "unsupported-input",
        "asset builds accept text grids and PNG sources",
        str(source),
    )
    return entries, report


def build_asset_atlas(
    source_dir: str | Path,
    palette: Palette,
    out_dir: str | Path,
    *,
    columns: int = 8,
) -> tuple[dict[str, Path], ValidationReport]:
    """Build a Phaser atlas and contact sheet from a mixed grid/PNG folder."""

    source = Path(source_dir)
    if not source.is_dir():
        raise PixelCoreError(f"asset folder not found: {source}")
    paths = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".grid", ".px", ".png"}
    )
    if not paths:
        raise PixelCoreError(f"no grid or PNG asset sources found under {source}")
    report = ValidationReport()
    entries: list[AtlasEntry] = []
    seen_names: dict[str, Path] = {}
    for path in paths:
        relative_name = path.relative_to(source).with_suffix("").as_posix()
        item_entries, item_report = load_asset_entries(
            path,
            palette,
            name=relative_name,
            require_png_sidecar=True,
        )
        report.extend(item_report)
        for entry in item_entries:
            if entry.name in seen_names:
                report.error(
                    "duplicate-frame",
                    f"atlas frame {entry.name!r} is already defined by {seen_names[entry.name]}",
                    str(path),
                )
                continue
            seen_names[entry.name] = path
            entries.append(entry)
    if not report.ok:
        return {}, report
    packed_entries = [(entry.name, entry.image) for entry in entries]
    atlas, frames = _pack_images(packed_entries, columns=columns)
    for entry in entries:
        frame = frames[entry.name]
        frame["category"] = entry.category
        if entry.origin is not None:
            frame["origin"] = {"x": entry.origin[0], "y": entry.origin[1]}
            frame["pivot"] = {
                "x": entry.origin[0] / entry.image.width,
                "y": entry.origin[1] / entry.image.height,
            }
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    png_path = destination / "assets.png"
    json_path = destination / "assets.json"
    preview_path = destination / "assets-preview.png"
    atlas.save(png_path, format="PNG", optimize=False)
    metadata = {
        "frames": frames,
        "meta": {
            "app": "tools/pixel-core",
            "format": "RGBA8888",
            "image": png_path.name,
            "scale": "1",
            "size": {"w": atlas.width, "h": atlas.height},
        },
    }
    json_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_preview(packed_entries, preview_path)
    return {"png": png_path, "json": json_path, "preview": preview_path}, report


def build_icon_atlas(
    source_dir: str | Path,
    palette: Palette,
    out_dir: str | Path,
    *,
    columns: int = 8,
) -> tuple[dict[str, Path], ValidationReport]:
    source = Path(source_dir)
    paths = sorted(path for path in source.rglob("*.txt") if path.is_file())
    if not paths:
        raise PixelCoreError(f"no .txt icon grids found under {source}")
    entries: list[tuple[str, Image.Image]] = []
    report = ValidationReport()
    seen_names: set[str] = set()
    for path in paths:
        asset = load_grid(path)
        item_report = validate_grid_asset(
            asset,
            palette,
            category=asset.category,
            require_category=True,
        )
        if asset.category != "icon":
            item_report.error(
                "icon-category",
                "HUD icon atlas inputs must declare category: icon",
                str(path),
            )
        report.extend(item_report)
        if not item_report.ok:
            continue
        if len(asset.frames) != 1:
            report.error("icon-frames", "icons must contain exactly one frame", str(path))
            continue
        name = path.stem
        if name in seen_names:
            report.error("duplicate-icon", f"duplicate icon name {name!r}", str(path))
            continue
        seen_names.add(name)
        entries.append((name, render_asset(asset, palette)))
    if not report.ok:
        return {}, report
    atlas, frames = _pack_images(entries, columns=columns)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    png_path = destination / "icons.png"
    json_path = destination / "icons.json"
    preview_path = destination / "icons-preview.png"
    atlas.save(png_path, format="PNG", optimize=False)
    metadata = {
        "frames": frames,
        "meta": {
            "app": "tools/pixel-core",
            "format": "RGBA8888",
            "image": png_path.name,
            "scale": "1",
            "size": {"w": atlas.width, "h": atlas.height},
        },
    }
    json_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_preview(entries, preview_path)
    return {"png": png_path, "json": json_path, "preview": preview_path}, report


def _parse_codepoint(value: str) -> int:
    clean = value.strip()
    if clean.upper().startswith("U+"):
        number = int(clean[2:], 16)
    elif clean.lower().startswith("0x"):
        number = int(clean, 16)
    elif clean.isdigit():
        number = int(clean)
    elif len(clean) == 1:
        number = ord(clean)
    elif len(clean) >= 3 and clean[0] == clean[-1] and clean[0] in {"'", '"'} and len(clean[1:-1]) == 1:
        number = ord(clean[1:-1])
    else:
        try:
            number = ord(unicodedata.lookup(clean.upper()))
        except (KeyError, TypeError) as exc:
            raise PixelCoreError(f"invalid codepoint {value!r}; use U+0041, 65, or one character") from exc
    if not 0 <= number <= 0x10FFFF or 0xD800 <= number <= 0xDFFF:
        raise PixelCoreError(f"invalid Unicode codepoint U+{number:04X}")
    return number


@dataclass(frozen=True)
class Glyph:
    name: str
    codepoint: int
    asset: GridAsset
    image: "Image.Image"
    advance: int
    baseline: int


def load_glyphs(
    source: str | Path, palette: Palette
) -> tuple[list[Glyph], ValidationReport]:
    source_path = Path(source)
    paths = [source_path] if source_path.is_file() else sorted(source_path.rglob("*.txt"))
    if not paths:
        raise PixelCoreError(f"no glyph grids found at {source_path}")
    report = ValidationReport()
    glyphs: list[Glyph] = []
    seen_codepoints: dict[int, Path] = {}
    for path in paths:
        asset = load_grid(path)
        item_report = validate_grid_asset(
            asset,
            palette,
            category=asset.category,
            require_category=True,
        )
        report.extend(item_report)
        codepoint_value = asset.metadata.get("codepoint")
        if not codepoint_value:
            report.error("missing-codepoint", "glyph needs a codepoint header", str(path))
            continue
        try:
            codepoint = _parse_codepoint(codepoint_value)
        except PixelCoreError as exc:
            report.error("bad-codepoint", str(exc), str(path))
            continue
        if codepoint > 0xFFFF:
            report.error(
                "unsupported-codepoint",
                f"minimal TTF exporter currently supports BMP codepoints only; got U+{codepoint:06X}",
                str(path),
            )
            continue
        if codepoint in seen_codepoints:
            report.error(
                "duplicate-codepoint",
                f"U+{codepoint:04X} is already defined by {seen_codepoints[codepoint]}",
                str(path),
            )
            continue
        if len(asset.frames) != 1:
            report.error("glyph-frames", "glyphs must contain exactly one frame", str(path))
            continue
        try:
            baseline = int(asset.metadata.get("baseline", str(asset.height - 2)))
            advance = int(asset.metadata.get("advance", str(asset.width)))
        except ValueError:
            report.error("bad-metrics", "baseline and advance must be integers", str(path))
            continue
        if not 0 <= baseline <= asset.height:
            report.error(
                "baseline-bounds",
                f"baseline {baseline} lies outside glyph height {asset.height}",
                str(path),
            )
        if advance <= 0:
            report.error("advance", "glyph advance must be positive", str(path))
        if not item_report.ok:
            continue
        seen_codepoints[codepoint] = path
        glyphs.append(
            Glyph(path.stem, codepoint, asset, render_asset(asset, palette), advance, baseline)
        )

    if glyphs:
        heights = {glyph.asset.height for glyph in glyphs}
        baselines = {glyph.baseline for glyph in glyphs}
        if len(heights) != 1:
            report.error("glyph-height", f"glyph heights differ: {sorted(heights)}", str(source_path))
        if len(baselines) != 1:
            report.error("glyph-baseline", f"glyph baselines differ: {sorted(baselines)}", str(source_path))
        digit_advances = {
            glyph.advance for glyph in glyphs if ord("0") <= glyph.codepoint <= ord("9")
        }
        if len(digit_advances) > 1:
            report.error(
                "tabular-digits",
                f"digit advances differ: {sorted(digit_advances)}",
                str(source_path),
            )
    glyphs.sort(key=lambda glyph: glyph.codepoint)
    return glyphs, report


def _font_slug(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return slug or "pixel-font"


def _font_atlas(
    glyphs: Sequence[Glyph], columns: int
) -> tuple["Image.Image", dict[int, tuple[int, int]]]:
    entries = [(f"U+{glyph.codepoint:04X}", glyph.image) for glyph in glyphs]
    atlas, frames = _pack_images(entries, columns=columns, padding=1)
    positions = {
        glyph.codepoint: (frames[f"U+{glyph.codepoint:04X}"]["frame"]["x"], frames[f"U+{glyph.codepoint:04X}"]["frame"]["y"])
        for glyph in glyphs
    }
    return atlas, positions


def _write_bmfont(
    glyphs: Sequence[Glyph],
    atlas: "Image.Image",
    positions: Mapping[int, tuple[int, int]],
    name: str,
    png_name: str,
    path: Path,
) -> None:
    baseline = max(glyph.baseline for glyph in glyphs)
    line_height = max(
        baseline - glyph.baseline + glyph.asset.height for glyph in glyphs
    )
    root = ET.Element("font")
    ET.SubElement(
        root,
        "info",
        {
            "face": name,
            "size": str(line_height),
            "bold": "0",
            "italic": "0",
            "charset": "",
            "unicode": "1",
            "stretchH": "100",
            "smooth": "0",
            "aa": "1",
            "padding": "0,0,0,0",
            "spacing": "1,1",
        },
    )
    ET.SubElement(
        root,
        "common",
        {
            "lineHeight": str(line_height),
            "base": str(baseline),
            "scaleW": str(atlas.width),
            "scaleH": str(atlas.height),
            "pages": "1",
            "packed": "0",
        },
    )
    pages = ET.SubElement(root, "pages")
    ET.SubElement(pages, "page", {"id": "0", "file": png_name})
    chars = ET.SubElement(root, "chars", {"count": str(len(glyphs))})
    for glyph in glyphs:
        x, y = positions[glyph.codepoint]
        ET.SubElement(
            chars,
            "char",
            {
                "id": str(glyph.codepoint),
                "x": str(x),
                "y": str(y),
                "width": str(glyph.asset.width),
                "height": str(glyph.asset.height),
                "xoffset": "0",
                "yoffset": str(baseline - glyph.baseline),
                "xadvance": str(glyph.advance),
                "page": "0",
                "chnl": "15",
            },
        )
    ET.indent(root, space="  ")
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def load_inline_icon_glyphs(
    source: str | Path,
    palette: Palette,
    *,
    start_codepoint: int = 0xE000,
    baseline: int = 10,
) -> tuple[list[Glyph], dict[str, str], ValidationReport]:
    """Load stable named 12x12 icons as private-use font glyphs."""

    source_path = Path(source)
    paths = sorted(source_path.rglob("*.txt"))
    if not paths:
        raise PixelCoreError(f"no inline icon grids found under {source_path}")
    report = ValidationReport()
    glyphs: list[Glyph] = []
    mapping: dict[str, str] = {}
    seen_names: set[str] = set()
    for index, path in enumerate(paths):
        asset = load_grid(path)
        item_report = validate_grid_asset(
            asset,
            palette,
            category=asset.category,
            require_category=True,
        )
        if asset.category != "inline-icon":
            item_report.error(
                "inline-icon-category",
                "inline font icons must declare category: inline-icon",
                str(path),
            )
        report.extend(item_report)
        name = path.stem
        if name in seen_names:
            report.error("duplicate-inline-icon", f"duplicate inline icon name {name!r}", str(path))
            continue
        seen_names.add(name)
        if len(asset.frames) != 1:
            report.error("inline-icon-frames", "inline icons must contain exactly one frame", str(path))
            continue
        codepoint = start_codepoint + index
        if codepoint > 0xF8FF:
            report.error("inline-icon-range", "inline icons exceed the BMP private-use range", str(path))
            continue
        if not item_report.ok:
            continue
        glyphs.append(
            Glyph(
                name,
                codepoint,
                asset,
                render_asset(asset, palette),
                asset.width,
                baseline,
            )
        )
        mapping[f"{{{name}}}"] = f"U+{codepoint:04X}"
    return glyphs, mapping, report


def _opaque_runs(glyph: Glyph) -> list[tuple[int, int, int]]:
    """Return horizontal opaque runs as (row, start, exclusive end)."""

    frame = glyph.asset.frames[0]
    runs: list[tuple[int, int, int]] = []
    for y, row in enumerate(frame):
        x = 0
        while x < len(row):
            if _opaque_name(glyph.asset, row[x]) is None:
                x += 1
                continue
            start = x
            x += 1
            while x < len(row) and _opaque_name(glyph.asset, row[x]) is not None:
                x += 1
            runs.append((y, start, x))
    return runs


def _glyph_binary(glyph: Glyph | None, unit: int = 100) -> tuple[bytes, tuple[int, int, int, int], int, int]:
    if glyph is None:
        return struct.pack(">hhhhhH", 0, 0, 0, 0, 0, 0), (0, 0, 0, 0), 0, 0
    points: list[tuple[int, int]] = []
    endpoints: list[int] = []
    for row, start, end in _opaque_runs(glyph):
        x0, x1 = start * unit, end * unit
        y0 = (glyph.baseline - row - 1) * unit
        y1 = (glyph.baseline - row) * unit
        points.extend(((x0, y0), (x0, y1), (x1, y1), (x1, y0)))
        endpoints.append(len(points) - 1)
    if not points:
        return struct.pack(">hhhhhH", 0, 0, 0, 0, 0, 0), (0, 0, 0, 0), 0, 0
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    bounds = min(x_values), min(y_values), max(x_values), max(y_values)
    data = bytearray(struct.pack(">hhhhh", len(endpoints), *bounds))
    data.extend(struct.pack(f">{len(endpoints)}H", *endpoints))
    data.extend(struct.pack(">H", 0))  # no instructions
    data.extend(bytes([0x01] * len(points)))  # on-curve, signed 16-bit deltas
    previous = 0
    for x, _ in points:
        data.extend(struct.pack(">h", x - previous))
        previous = x
    previous = 0
    for _, y in points:
        data.extend(struct.pack(">h", y - previous))
        previous = y
    return bytes(data), bounds, len(points), len(endpoints)


def _table_checksum(data: bytes) -> int:
    padded = data + b"\0" * ((4 - len(data) % 4) % 4)
    return sum(struct.unpack(f">{len(padded) // 4}I", padded)) & 0xFFFFFFFF


def _build_cmap(codepoint_to_gid: Mapping[int, int]) -> bytes:
    pairs = sorted(codepoint_to_gid.items())
    end_codes = [codepoint for codepoint, _ in pairs] + [0xFFFF]
    start_codes = list(end_codes)
    deltas = [((gid - codepoint) & 0xFFFF) for codepoint, gid in pairs] + [1]
    offsets = [0] * len(end_codes)
    seg_count = len(end_codes)
    power = 1 << (seg_count.bit_length() - 1)
    search_range = 2 * power
    entry_selector = power.bit_length() - 1
    range_shift = 2 * seg_count - search_range
    length = 16 + 8 * seg_count
    subtable = bytearray(
        struct.pack(
            ">HHHHHHH",
            4,
            length,
            0,
            seg_count * 2,
            search_range,
            entry_selector,
            range_shift,
        )
    )
    subtable.extend(struct.pack(f">{seg_count}H", *end_codes))
    subtable.extend(struct.pack(">H", 0))
    subtable.extend(struct.pack(f">{seg_count}H", *start_codes))
    subtable.extend(struct.pack(f">{seg_count}H", *deltas))
    subtable.extend(struct.pack(f">{seg_count}H", *offsets))
    return struct.pack(">HHHHI", 0, 1, 3, 1, 12) + bytes(subtable)


def _build_name_table(family: str) -> bytes:
    postscript = re.sub(r"[^A-Za-z0-9-]", "", family.replace(" ", "-")) or "PixelFont"
    values = {1: family, 2: "Regular", 4: f"{family} Regular", 6: postscript}
    records: list[tuple[int, int, int, int, bytes]] = []
    for name_id, value in values.items():
        encoded = value.encode("utf-16-be")
        records.append((3, 1, 0x0409, name_id, encoded))
    records.sort(key=lambda record: record[:4])
    count = len(records)
    string_offset = 6 + count * 12
    storage = bytearray()
    record_data = bytearray()
    for platform, encoding, language, name_id, encoded in records:
        offset = len(storage)
        storage.extend(encoded)
        record_data.extend(
            struct.pack(">HHHHHH", platform, encoding, language, name_id, len(encoded), offset)
        )
    return struct.pack(">HHH", 0, count, string_offset) + bytes(record_data) + bytes(storage)


def build_ttf(glyphs: Sequence[Glyph], name: str, output: str | Path) -> Path:
    if not glyphs:
        raise PixelCoreError("cannot build a font without glyphs")
    unit = 100
    glyph_data: list[bytes] = []
    loca_offsets = [0]
    bounds: list[tuple[int, int, int, int]] = []
    max_points = max_contours = 0
    for glyph in [None, *glyphs]:
        binary, glyph_bounds, points, contours = _glyph_binary(glyph, unit)
        binary += b"\0" * ((4 - len(binary) % 4) % 4)
        glyph_data.append(binary)
        loca_offsets.append(loca_offsets[-1] + len(binary))
        bounds.append(glyph_bounds)
        max_points = max(max_points, points)
        max_contours = max(max_contours, contours)
    glyf = b"".join(glyph_data)
    loca = struct.pack(f">{len(loca_offsets)}I", *loca_offsets)
    glyph_count = len(glyphs) + 1
    codepoint_to_gid = {glyph.codepoint: index + 1 for index, glyph in enumerate(glyphs)}
    advances = [max(glyph.advance for glyph in glyphs) * unit] + [glyph.advance * unit for glyph in glyphs]
    hmtx = b"".join(struct.pack(">Hh", advance, 0) for advance in advances)
    x_min = min(bound[0] for bound in bounds)
    y_min = min(bound[1] for bound in bounds)
    x_max = max(bound[2] for bound in bounds)
    y_max = max(bound[3] for bound in bounds)
    ascent = max(glyph.baseline for glyph in glyphs) * unit
    descent = -max(glyph.asset.height - glyph.baseline for glyph in glyphs) * unit
    advance_max = max(advances)
    head = struct.pack(
        ">IIIIHHQQhhhhHHhhh",
        0x00010000,
        0x00010000,
        0,
        0x5F0F3CF5,
        0x000B,
        1000,
        0,
        0,
        x_min,
        y_min,
        x_max,
        y_max,
        0,
        8,
        2,
        1,
        0,
    )
    hhea = (
        struct.pack(">I", 0x00010000)
        + struct.pack(">hhhH", ascent, descent, 0, advance_max)
        + struct.pack(">hhh", 0, 0, x_max)
        + struct.pack(">hhh", 1, 0, 0)
        + struct.pack(">hhhh", 0, 0, 0, 0)
        + struct.pack(">hH", 0, glyph_count)
    )
    maxp = struct.pack(
        ">IH13H",
        0x00010000,
        glyph_count,
        max_points,
        max_contours,
        0,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    average_advance = round(sum(advances[1:]) / max(1, len(advances) - 1))
    first_char = min(codepoint_to_gid)
    last_char = max(codepoint_to_gid)
    os2 = (
        struct.pack(">HhHHH", 0, average_advance, 400, 5, 0)
        + struct.pack(">11h", 650, 600, 0, 75, 650, 600, 0, 350, 50, 250, 0)
        + bytes((0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        + struct.pack(">IIII", 1, 0, 0, 0)
        + b"AAWY"
        + struct.pack(">HHH", 0x0040, first_char, last_char)
        + struct.pack(">hhh", ascent, descent, 0)
        + struct.pack(">HH", max(0, ascent), max(0, -descent))
    )
    post = struct.pack(">IIhhIIIII", 0x00030000, 0, -100, 50, 1, 0, 0, 0, 0)
    tables: dict[bytes, bytes] = {
        b"OS/2": os2,
        b"cmap": _build_cmap(codepoint_to_gid),
        b"glyf": glyf,
        b"head": head,
        b"hhea": hhea,
        b"hmtx": hmtx,
        b"loca": loca,
        b"maxp": maxp,
        b"name": _build_name_table(name),
        b"post": post,
    }
    tags = sorted(tables)
    count = len(tags)
    power = 1 << (count.bit_length() - 1)
    header = struct.pack(">IHHHH", 0x00010000, count, power * 16, power.bit_length() - 1, count * 16 - power * 16)
    offset = 12 + count * 16
    records = bytearray()
    body = bytearray()
    offsets: dict[bytes, int] = {}
    for tag in tags:
        data = tables[tag]
        offsets[tag] = offset
        records.extend(struct.pack(">4sIII", tag, _table_checksum(data), offset, len(data)))
        body.extend(data)
        padding = (4 - len(data) % 4) % 4
        body.extend(b"\0" * padding)
        offset += len(data) + padding
    font = bytearray(header + bytes(records) + bytes(body))
    adjustment = (0xB1B0AFBA - _table_checksum(bytes(font))) & 0xFFFFFFFF
    struct.pack_into(">I", font, offsets[b"head"] + 8, adjustment)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(font))
    return output_path


def write_font_specimen(atlas: "Image.Image", output: str | Path) -> Path:
    return write_preview((("glyph atlas", atlas),), output, scales=(1, 2, 4))


def build_font(
    source: str | Path,
    palette: Palette,
    out_dir: str | Path,
    *,
    name: str | None = None,
    columns: int = 16,
    inline_icons: str | Path | None = None,
) -> tuple[dict[str, Path], ValidationReport]:
    glyphs, report = load_glyphs(source, palette)
    if not report.ok:
        return {}, report
    if not glyphs:
        raise PixelCoreError("no valid glyphs were found")
    source_path = Path(source)
    if name:
        font_name = name
    else:
        font_name = (source_path.parent.name if source_path.is_file() else source_path.name)
        font_name = font_name.replace("-", " ").replace("_", " ").title()
    inline_mapping: dict[str, str] = {}
    if inline_icons is not None:
        icon_baseline = max(glyph.baseline for glyph in glyphs) + 2
        icon_glyphs, inline_mapping, icon_report = load_inline_icon_glyphs(
            inline_icons,
            palette,
            baseline=icon_baseline,
        )
        report.extend(icon_report)
        occupied = {glyph.codepoint for glyph in glyphs}
        collisions = occupied & {glyph.codepoint for glyph in icon_glyphs}
        if collisions:
            report.error(
                "inline-icon-codepoint",
                "inline icon private-use codepoints collide with font glyphs: "
                + ", ".join(f"U+{value:04X}" for value in sorted(collisions)),
                str(inline_icons),
            )
        if report.errors:
            return {}, report
        glyphs.extend(icon_glyphs)
        glyphs.sort(key=lambda glyph: glyph.codepoint)
    slug = _font_slug(font_name)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    png_path = destination / f"{slug}.png"
    fnt_path = destination / f"{slug}.fnt"
    ttf_path = destination / f"{slug}.ttf"
    specimen_path = destination / f"{slug}-specimen.png"
    inline_path = destination / "inline-icons.json"
    atlas, positions = _font_atlas(glyphs, columns)
    atlas.save(png_path, format="PNG", optimize=False)
    _write_bmfont(glyphs, atlas, positions, font_name, png_path.name, fnt_path)
    build_ttf(glyphs, font_name, ttf_path)
    write_font_specimen(atlas, specimen_path)
    outputs = {
        "png": png_path,
        "fnt": fnt_path,
        "ttf": ttf_path,
        "specimen": specimen_path,
    }
    if inline_icons is not None:
        inline_path.write_text(
            json.dumps(inline_mapping, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        outputs["inline-icons"] = inline_path
    return outputs, report
