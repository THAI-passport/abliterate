#!/usr/bin/env python3
"""Command-line entry point for the shared pixel asset core."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from pixel_core import (
    PixelCoreError,
    ValidationReport,
    build_asset_atlas,
    build_font,
    build_icon_atlas,
    convert_image,
    export_palette,
    format_grid,
    load_grid,
    load_palette,
    load_preview_image,
    palette_for_semantics,
    parse_grid_text,
    parse_origin,
    parse_size,
    render_asset,
    save_render,
    validate_grid_asset,
    validate_palette,
    validate_png,
    write_animation_preview,
    write_conversion_preview,
    write_preview,
)


def _print_report(report: ValidationReport) -> None:
    if report.issues:
        print(report.format())


def _load_checked_palette(path: str) -> tuple[object, ValidationReport]:
    palette = load_palette(path)
    report = validate_palette(palette)
    return palette, report


def command_palette_export(args: argparse.Namespace) -> int:
    palette, report = _load_checked_palette(args.palette)
    _print_report(report)
    if report.errors:
        return 1
    outputs = export_palette(palette, args.out_dir, basename=args.basename)
    for kind, path in outputs.items():
        print(f"{kind}: {path}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    report = ValidationReport()
    report.extend(palette_report)
    for value in args.paths:
        path = Path(value)
        suffix = path.suffix.lower()
        try:
            if suffix in {".txt", ".grid", ".px"}:
                report.extend(validate_grid_asset(load_grid(path), palette, category=args.category))
            elif suffix == ".png":
                report.extend(validate_png(path, palette, category=args.category))
            else:
                report.error(
                    "unsupported-input",
                    "validation accepts text grids and PNG files",
                    str(path),
                )
        except PixelCoreError as exc:
            report.error("parse", str(exc), str(path))
    _print_report(report)
    if report.errors:
        print(
            f"validation failed: {len(report.errors)} error(s), {len(report.warnings)} warning(s)",
            file=sys.stderr,
        )
        return 1
    print(f"validation passed: {len(report.warnings)} warning(s)")
    return 0


def command_render(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    asset = load_grid(args.grid)
    report = validate_grid_asset(asset, palette, category=args.category)
    report.extend(palette_report)
    _print_report(report)
    if report.errors:
        return 1
    path = save_render(asset, palette, args.output, scale=args.scale)
    print(path)
    return 0


def command_preview(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    report = ValidationReport()
    report.extend(palette_report)
    entries = []
    for value in args.inputs:
        image, item_report = load_preview_image(value, palette)
        report.extend(item_report)
        if item_report.ok:
            entries.append((Path(value).stem, image))
    _print_report(report)
    if report.errors:
        return 1
    path = write_preview(entries, args.output)
    print(path)
    return 0


def command_asset_build(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    asset = load_grid(args.grid)
    report = validate_grid_asset(
        asset,
        palette,
        category=args.category,
        require_category=True,
    )
    report.extend(palette_report)
    _print_report(report)
    if report.errors:
        return 1
    destination = Path(args.out_dir)
    png_path = destination / f"{Path(args.grid).stem}.png"
    preview_path = destination / f"{Path(args.grid).stem}-preview.png"
    save_render(asset, palette, png_path)
    # The validated source grid carries semantic declarations that a bare
    # rendered PNG cannot. Reuse that source for the preview instead of
    # re-validating the intermediate PNG without its metadata.
    image = render_asset(asset, palette)
    write_preview(((Path(args.grid).stem, image),), preview_path)
    print(f"png: {png_path}")
    print(f"preview: {preview_path}")
    if len(asset.frames) > 1:
        animation_path = destination / f"{Path(args.grid).stem}-animated.gif"
        write_animation_preview(asset, palette, animation_path)
        print(f"animation: {animation_path}")
    return 0


def command_build_assets(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    _print_report(palette_report)
    if palette_report.errors:
        return 1
    outputs, report = build_asset_atlas(
        args.source,
        palette,
        args.out_dir,
        columns=args.columns,
    )
    _print_report(report)
    if report.errors:
        return 1
    for kind, path in outputs.items():
        print(f"{kind}: {path}")
    return 0


def command_build_icons(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    _print_report(palette_report)
    if palette_report.errors:
        return 1
    outputs, report = build_icon_atlas(
        args.source, palette, args.out_dir, columns=args.columns
    )
    _print_report(report)
    if report.errors:
        return 1
    for kind, path in outputs.items():
        print(f"{kind}: {path}")
    return 0


def command_build_font(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    _print_report(palette_report)
    if palette_report.errors:
        return 1
    outputs, report = build_font(
        args.source,
        palette,
        args.out_dir,
        name=args.name,
        columns=args.columns,
        inline_icons=args.inline_icons,
    )
    _print_report(report)
    if report.errors:
        return 1
    for kind, path in outputs.items():
        print(f"{kind}: {path}")
    return 0


def command_convert(args: argparse.Namespace) -> int:
    palette, palette_report = _load_checked_palette(args.palette)
    _print_report(palette_report)
    if palette_report.errors:
        return 1
    size = parse_size(args.size)
    origin = parse_origin(args.origin) if args.origin else None
    semantic_palette = palette_for_semantics(palette, args.semantic)
    original, mapped, grid = convert_image(
        args.image,
        semantic_palette,
        size,
        crop=args.crop,
        dither=args.dither,
        dither_strength=args.dither_strength,
        alpha_threshold=args.alpha_threshold,
    )
    extra_metadata = None
    if args.semantic:
        extra_metadata = {"semantic": ",".join(sorted(set(args.semantic)))}
    grid_text = format_grid(
        grid,
        palette,
        category=args.category,
        origin=origin,
        extra_metadata=extra_metadata,
    )
    grid_path = Path(args.output_grid)
    png_path = Path(args.output_png)
    generated_asset = parse_grid_text(grid_text, source=grid_path)
    generated_report = validate_grid_asset(
        generated_asset,
        palette,
        require_category=True,
    )
    _print_report(generated_report)
    if generated_report.errors:
        return 1
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    grid_path.write_text(grid_text, encoding="utf-8")
    mapped.save(png_path, format="PNG", optimize=False)
    preview_path = write_conversion_preview(original, mapped, args.preview)
    generated_report.extend(validate_png(png_path, palette))
    if generated_report.errors:
        _print_report(generated_report)
        return 1
    print(f"grid: {grid_path}")
    print(f"png: {png_path}")
    print(f"preview: {preview_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, render, preview, and build locked-palette pixel assets."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    palette_export = subparsers.add_parser(
        "palette-export", help="derive .hex, .gpl, and swatch.png from palette JSON"
    )
    palette_export.add_argument("--palette", required=True)
    palette_export.add_argument("--out-dir", required=True)
    palette_export.add_argument("--basename")
    palette_export.set_defaults(function=command_palette_export)

    validate = subparsers.add_parser("validate", help="validate text grids or indexed PNGs")
    validate.add_argument("paths", metavar="PATH", nargs="+")
    validate.add_argument("--palette", required=True)
    validate.add_argument("--category")
    validate.set_defaults(function=command_validate)

    render = subparsers.add_parser("render", help="render a text grid to PNG")
    render.add_argument("grid", metavar="GRID")
    render.add_argument("--palette", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--scale", type=int, default=1)
    render.add_argument("--category")
    render.set_defaults(function=command_render)

    preview = subparsers.add_parser(
        "preview", help="make a 1x/4x contact sheet from grids or PNGs"
    )
    preview.add_argument("inputs", metavar="INPUT", nargs="+")
    preview.add_argument("--palette", required=True)
    preview.add_argument("--output", required=True)
    preview.set_defaults(function=command_preview)

    asset_build = subparsers.add_parser(
        "asset-build", help="validate one grid and write its PNG and 1x/4x preview"
    )
    asset_build.add_argument("grid", metavar="GRID")
    asset_build.add_argument("--palette", required=True)
    asset_build.add_argument("--out-dir", required=True)
    asset_build.add_argument("--category")
    asset_build.set_defaults(function=command_asset_build)

    assets = subparsers.add_parser(
        "build-assets",
        aliases=["asset-atlas"],
        help="build a Phaser atlas and 1x/4x preview from a mixed grid/PNG folder",
    )
    assets.add_argument("source", metavar="DIR")
    assets.add_argument("--palette", required=True)
    assets.add_argument("--out-dir", required=True)
    assets.add_argument("--columns", type=int, default=8)
    assets.set_defaults(function=command_build_assets)

    icons = subparsers.add_parser(
        "build-icons", aliases=["icon-build"], help="build the icon PNG/JSON atlas and preview"
    )
    icons.add_argument("source", metavar="DIR")
    icons.add_argument("--palette", required=True)
    icons.add_argument("--out-dir", required=True)
    icons.add_argument("--columns", type=int, default=8)
    icons.set_defaults(function=command_build_icons)

    font = subparsers.add_parser(
        "build-font", aliases=["font-build"], help="build BMFont, TTF, and a specimen sheet"
    )
    font.add_argument("source", metavar="FONT_SOURCE_OR_DIR")
    font.add_argument("--palette", required=True)
    font.add_argument("--out-dir", required=True)
    font.add_argument("--name")
    font.add_argument("--columns", type=int, default=16)
    font.add_argument("--inline-icons", metavar="DIR")
    font.set_defaults(function=command_build_font)

    convert = subparsers.add_parser(
        "convert", help="area-resize and map a licensed reference image to the palette"
    )
    convert.add_argument("image", metavar="IMAGE")
    convert.add_argument("--palette", required=True)
    convert.add_argument("--size", required=True, help="target WIDTHxHEIGHT")
    convert.add_argument("--output-grid", required=True)
    convert.add_argument("--output-png", required=True)
    convert.add_argument("--preview", required=True)
    convert.add_argument("--dither", action="store_true", help="apply deterministic 4x4 Bayer dithering")
    convert.add_argument("--dither-strength", type=int, default=24)
    convert.add_argument("--alpha-threshold", type=int, default=128)
    convert.add_argument("--crop", choices=("cover", "fit"), default="cover")
    convert.add_argument("--category", default="icon")
    convert.add_argument("--origin", help="anchor as X,Y for a world-placed result")
    convert.add_argument(
        "--semantic",
        action="append",
        choices=("money", "ruin", "skin"),
        default=[],
        help="allow and declare a reserved meaning ramp; repeat for more than one",
    )
    convert.set_defaults(function=command_convert)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.function(args))
    except PixelCoreError as exc:
        print(f"ERROR [pixel-core] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR [pixel-core] interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
