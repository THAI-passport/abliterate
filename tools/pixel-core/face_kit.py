#!/usr/bin/env python3
"""The face kit: hand-drawn head outlines and face parts snapped into slots.

Every pixel in `art/src/rig/face-kit/` is hand-typed as a text grid. This
module only ever *places* those grids: it reads `kit.json`, blits part patches
at their slot anchors, recolours them per skin and hair ramp, and renders
review sheets. It draws no geometry of its own: no formula ever produces a
pixel that is not present in a checked-in grid.

Slot schema (kit.json):

    builds.<build>.<direction>.head    default head outline grid for that view
    builds.<build>.<direction>.heads   shape -> hand-drawn outline grid
    builds.<build>.<direction>.slots   part name -> [x, y] anchor on the head
    parts.<part>.group                 "skin" | "hair" | "none": recolour group
    parts.<part>.styles                the style keys available for the part
    parts.<part>.reserved              true when a reservation applies
    faces.<name>                       {part: style, ...}; "head" selects the shape
                                        and "nose": false opts out
    reserved.<part/style>              allow-list of appearance name patterns

Part files live at `parts/<part>-<style>.<direction>.txt` and are blitted with
their top-left pixel at the slot anchor. `up` has no face slots: the back of
the head keeps the volume and shows no face.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Mapping, Sequence

import pixel_tech as pt
from pixel_core import load_palette

DIRECTIONS = ("down", "up", "left", "right")
CONTEXTS = ("sprite", "portrait")


class FaceKitError(pt.PixelTechError):
    pass


class FaceKit:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.data = json.loads((self.root / "kit.json").read_text(encoding="utf-8"))
        palette_path = self.root / self.data.get("palette", "../../../palette/game.json")
        if not palette_path.exists():
            palette_path = Path(self.data["palette"])
        self.palette = load_palette(palette_path)
        self.swaps = pt.expand_swaps(
            json.loads((self.root / self.data["swaps"]).read_text(encoding="utf-8")), self.palette
        )

    # --- lookups -----------------------------------------------------------

    def builds(self) -> list[str]:
        return list(self.data["builds"])

    def faces(self) -> dict[str, dict]:
        return self.data["faces"]

    def head_shapes(self, build: str) -> list[str]:
        view = self.data["builds"][build]["down"]
        if "heads" in view:
            return list(view["heads"])
        return [self.data.get("defaults", {}).get("head", "default")]

    def head_path(self, build: str, direction: str, shape: str | None = None) -> Path:
        try:
            view = self.data["builds"][build][direction]
            if "heads" in view:
                selected = shape or self.data.get("defaults", {}).get("head", "round")
                return self.root / view["heads"][selected]
            return self.root / view["head"]
        except KeyError as exc:
            raise FaceKitError(
                f"face kit {self.root.name}: no {shape or 'default'} {direction} head for {build}"
            ) from exc

    def head_pivot(self, build: str, direction: str, shape: str | None = None) -> str:
        return pt.read_grid(self.head_path(build, direction, shape), self.palette).headers.get("pivot", "0,0")

    def slots(self, build: str, direction: str) -> dict[str, list[int]]:
        return self.data["builds"][build][direction].get("slots", {})

    def part_group(self, part: str) -> str:
        return self.data["parts"][part].get("group", "none")

    def part_path(self, part: str, style: str, direction: str, build: str = "") -> Path:
        """Part grids, with an optional per-build override (eye spacing differs
        between builds, so `eyes-dot.body-a.down.txt` beats `eyes-dot.down.txt`)."""

        candidates = [f"{part}-{style}.{direction}.txt"]
        if build:
            candidates.insert(0, f"{part}-{style}.{build}.{direction}.txt")
        for name in candidates:
            path = self.root / "parts" / name
            if path.exists():
                return path
        raise FaceKitError(
            f"face kit {self.root.name}: missing part {part}-{style} for {build or 'any build'}.{direction}"
        )

    # --- composition -------------------------------------------------------

    def _recolour(self, grid: pt.NameGrid, group: str, skin: str, hair: str) -> pt.NameGrid:
        mapping: dict[str, str] = {}
        if group == "skin":
            mapping = self.swaps["skin"][skin]
        elif group == "hair":
            mapping = self.swaps["hair"][hair]
        return pt.recolor(grid, mapping) if mapping else [row[:] for row in grid]

    def allowing(self, face: Mapping[str, str | bool]) -> str:
        """An appearance name permitted to wear this face spec (for sheets and
        layer builders composing the whole kit); empty when nothing is reserved."""

        for part, style in face.items():
            if part == "head":
                continue
            allowed = self.data.get("reserved", {}).get(f"{part}/{style}")
            if allowed:
                return allowed[0]
        return ""

    def _check_reservation(self, requested: Mapping[str, str], appearance: str, context: str) -> None:
        if context == "portrait":
            return  # Portraits carry all expression (character_design.md section 8).
        for part, style in sorted(requested.items()):
            allowed = self.data.get("reserved", {}).get(f"{part}/{style}")
            if allowed is None:
                continue
            if not any(fnmatch.fnmatch(appearance or "", pattern) for pattern in allowed):
                raise FaceKitError(
                    f"face part {part}/{style} is reserved for {allowed}; "
                    f"appearance {appearance!r} is not on the allow-list"
                )

    def compose(
        self,
        build: str,
        direction: str,
        face: Mapping[str, str | bool],
        *,
        skin: str = "light",
        hair: str = "black",
        appearance: str = "",
        context: str = "sprite",
    ) -> pt.NameGrid:
        """Blit the requested face parts onto the head outline at their slots.

        Raises FaceKitError when a reserved part is off its allow-list, a part
        falls outside the head, or a part pixel lands on a transparent head
        pixel. Same inputs always give the same grid.
        """

        if context not in CONTEXTS:
            raise FaceKitError(f"unknown context {context!r}")
        head_choice = face.get("head", self.data.get("defaults", {}).get("head", "round"))
        overlay_only = head_choice is False
        shape = str(self.data.get("defaults", {}).get("head", "round") if overlay_only else head_choice)
        if shape not in self.head_shapes(build):
            raise FaceKitError(f"face kit {self.root.name}: unknown head shape {shape!r} for {build}")
        head_grid = pt.read_grid(self.head_path(build, direction, shape), self.palette).frames[0]
        head_mask = self._recolour(head_grid, "skin", skin, hair)
        head = pt.blank(len(head_mask[0]), len(head_mask)) if overlay_only else [row[:] for row in head_mask]
        height, width = len(head), len(head[0])
        slots = self.slots(build, direction)
        requested = {
            part: style for part, style in face.items()
            if part != "head" and isinstance(style, str)
        }
        # The nose is part of every face unless the face opts out.
        if face.get("nose", True) is not False:
            default_nose = self.data.get("defaults", {}).get("nose", "on")
            requested.setdefault("nose", default_nose)
        self._check_reservation(requested, appearance, context)
        for part, style in sorted(requested.items()):
            if part not in self.data["parts"]:
                raise FaceKitError(f"face kit {self.root.name}: unknown part {part!r}")
            if style not in self.data["parts"][part]["styles"]:
                raise FaceKitError(f"face kit {self.root.name}: part {part} has no style {style!r}")
            if part not in slots:
                continue  # Nothing visible from this direction (e.g. `up`).
            patch = pt.read_grid(self.part_path(part, style, direction, build), self.palette).frames[0]
            patch = self._recolour(patch, self.part_group(part), skin, hair)
            ax, ay = slots[part]
            ph, pw = len(patch), len(patch[0])
            if ay + ph > height or ax + pw > width:
                raise FaceKitError(
                    f"{build}/{direction}: part {part}-{style} at [{ax},{ay}] "
                    f"falls outside the {width}x{height} head"
                )
            for y in range(ph):
                for x in range(pw):
                    if patch[y][x] is not None and head_mask[ay + y][ax + x] is None:
                        raise FaceKitError(
                            f"{build}/{direction}: part {part}-{style} lands on a "
                            f"transparent head pixel at head [{ax + x},{ay + y}]"
                        )
            pt.blit(head, patch, ax, ay)
        return head

    # --- rig output --------------------------------------------------------

    def write_layer(
        self,
        rig_root: Path,
        build: str,
        name: str,
        face: Mapping[str, str | bool],
        *,
        skin: str = "light",
        hair: str = "black",
        appearance: str = "",
        context: str = "sprite",
    ) -> Path:
        """Write the composed face as a rig layer: layers/<name>/head.<dir>.txt."""

        head_choice = face.get("head", self.data.get("defaults", {}).get("head", "round"))
        overlay_only = head_choice is False
        shape = str(self.data.get("defaults", {}).get("head", "round") if overlay_only else head_choice)
        pivot = self.head_pivot(build, "down", shape)
        folder = Path(rig_root) / build / "layers" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "layer.json").write_text(
            json.dumps(
                {"z": "top" if overlay_only else "part", "mode": "over" if overlay_only else "replace",
                 "all_directions": True},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        for direction in DIRECTIONS:
            grid = self.compose(
                build, direction, face, skin=skin, hair=hair, appearance=appearance, context=context
            )
            comment = f"face {name} on {build}, {direction}; composed by face-compose."
            (folder / f"head.{direction}.txt").write_text(
                pt.format_frames([grid], self.palette, {"pivot": pivot, "semantic": "skin"}, [f"# {comment}"]),
                encoding="utf-8",
            )
        return folder

    def install_heads(self, rig_root: Path) -> list[Path]:
        """Copy the kit's head outlines into the rigs as the head parts."""

        written = []
        for build in self.builds():
            for direction in DIRECTIONS:
                grid = pt.read_grid(self.head_path(build, direction), self.palette)
                target = Path(rig_root) / build / "parts" / f"head.{direction}.txt"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    pt.format_frames([grid.frames[0]], self.palette, dict(grid.headers), list(grid.comments)),
                    encoding="utf-8",
                )
                written.append(target)
        return written


# --- sheets -----------------------------------------------------------------


def _cell(
    kit: FaceKit,
    build: str,
    direction: str,
    face_name: str,
    skin: str,
    background: pt.NameGrid | None,
):
    from PIL import Image

    grid = kit.compose(build, direction, kit.faces()[face_name], skin=skin,
                       appearance=kit.allowing(kit.faces()[face_name]))
    # The rig outlines every composed figure; judge the head as it will appear.
    grid = pt.add_outline(grid, "ink-1")
    image = pt.to_image(grid, kit.palette)
    if background is not None:
        tile = pt.to_image(background, kit.palette)
        carpet = Image.new("RGBA", image.size, (0, 0, 0, 255))
        for y in range(0, carpet.height, tile.height):
            for x in range(0, carpet.width, tile.width):
                carpet.alpha_composite(tile, (x, y))
        carpet.alpha_composite(image)
        image = carpet
    return image


def face_sheet(
    kit: FaceKit,
    output: Path,
    *,
    skins: Sequence[str],
    carpets: Sequence[Path] | None = None,
    carpet_faces: Sequence[str] | None = None,
) -> Path:
    """One labelled sheet: rows are faces, columns are skins, per build, 1x and 4x.

    With `carpets`, a companion `<stem>-carpet.png` repeats the named faces on
    each front carpet, so readability is judged in context.
    """

    from PIL import Image, ImageDraw

    faces = list(kit.faces())
    builds = kit.builds()
    cell_w, cell_h, label_w, gap = 18, 17, 150, 8
    width = label_w + len(skins) * cell_w + gap
    height = len(builds) * (len(faces) * cell_h + 22) + gap
    image = Image.new("RGBA", (width, height), (40, 42, 54, 255))
    draw = ImageDraw.Draw(image)
    y = gap
    for build in builds:
        draw.text((4, y), f"{build} (down)", fill=(236, 229, 218, 255))
        draw.text((label_w, y), "columns: " + " / ".join(skins), fill=(168, 164, 152, 255))
        y += 14
        y += 12
        for f, face_name in enumerate(faces):
            draw.text((4, y + 2), face_name, fill=(236, 229, 218, 255))
            for s, skin in enumerate(skins):
                image.alpha_composite(_cell(kit, build, "down", face_name, skin, None), (label_w + s * cell_w, y))
            y += cell_h
        y += 8
    pt.save_png(pt.one_and_four(image), output)

    if carpets:
        carpet_output = output.parent / f"{output.stem}-carpet{output.suffix}"
        names = list(carpet_faces or faces)
        width2 = label_w + len(names) * len(carpets) * cell_w + gap
        height2 = len(builds) * (len(names) * cell_h + 22) + gap
        sheet = Image.new("RGBA", (width2, height2), (40, 42, 54, 255))
        d2 = ImageDraw.Draw(sheet)
        tiles = [pt.read_grid(path, kit.palette).frames[0] for path in carpets]
        y = gap
        for build in builds:
            d2.text((4, y), f"{build} (down, on the front carpets)", fill=(236, 229, 218, 255))
            y += 14
            for f, face_name in enumerate(names):
                d2.text((4, y + 2), face_name, fill=(236, 229, 218, 255))
                for c, carpet in enumerate(carpets):
                    for s, skin in enumerate(skins):
                        x = label_w + (c * len(skins) + s) * cell_w
                        sheet.alpha_composite(_cell(kit, build, "down", face_name, skin, tiles[c]), (x, y))
                y += cell_h
            y += 8
        pt.save_png(pt.one_and_four(sheet), carpet_output)


def directions_sheet(kit: FaceKit, output: Path, *, face_name: str = "brows", skin: str = "light") -> Path:
    """One face in all four directions per build, 1x and 4x, labelled."""

    from PIL import Image, ImageDraw

    builds = kit.builds()
    cell_w, cell_h, label_w, gap = 34, 15, 100, 6
    width = label_w + len(DIRECTIONS) * cell_w + gap
    height = len(builds) * (cell_h + 16) + gap
    image = Image.new("RGBA", (width, height), (40, 42, 54, 255))
    draw = ImageDraw.Draw(image)
    y = gap
    for build in builds:
        draw.text((4, y + 1), build, fill=(236, 229, 218, 255))
        for index, direction in enumerate(DIRECTIONS):
            grid = kit.compose(build, direction, kit.faces()[face_name], skin=skin,
                               appearance=kit.allowing(kit.faces()[face_name]))
            # The rig outlines every composed figure; judge the head as it appears.
            grid = pt.add_outline(grid, "ink-1")
            image.alpha_composite(pt.to_image(grid, kit.palette), (label_w + index * cell_w, y))
            draw.text((label_w + index * cell_w, y + cell_h + 2), direction, fill=(168, 164, 152, 255))
        y += cell_h + 16
    pt.save_png(pt.one_and_four(image), output)
