#!/usr/bin/env python3
"""
Portable Windows packaging for downloaded Chromium binaries.

This module creates portable ZIP packages from downloaded pre-built
Chromium binaries (chrome-win), as opposed to the standard windows.py
module which expects a compiled build with mini_installer.exe.

Use this when:
- Using chromium_download module (downloaded binaries)
- Want a portable .zip package without installer

Output:
- NexusOS_vX.X.X_x64.zip - Portable package (extract and run)
"""

import shutil
import zipfile
from pathlib import Path
from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.registry import build_module
from ...common.utils import (
    log_info,
    log_error,
    log_success,
    log_warning,
)
from ...common.notify import get_notifier, COLOR_GREEN


@build_module(
    name="portable_windows",
    phase="package",
    requires=[],
    produces=["portable_zip"],
    description="Create portable Windows ZIP from downloaded Chromium",
    platform="windows",
)
class PortableWindowsPackageModule(CommandModule):
    produces = ["portable_zip"]
    requires = []
    description = "Create portable Windows ZIP from downloaded Chromium"

    def validate(self, ctx: Context) -> None:
        # Check if chrome.exe exists (from downloaded binary)
        chrome_exe = ctx.chromium_src / "chrome.exe"

        if not chrome_exe.exists():
            raise ValidationError(
                f"chrome.exe not found: {chrome_exe}\n"
                "This module requires a downloaded Chromium binary.\n"
                "Run with --modules chromium_download,resources,portable_windows"
            )

    def execute(self, ctx: Context) -> None:
        log_info("\n📦 Creating portable Windows package...")

        zip_path = self._create_portable_zip(ctx)

        ctx.artifact_registry.add("portable_zip", zip_path)

        log_success("Portable Windows package created successfully")

        # Send notification
        notifier = get_notifier()
        notifier.notify(
            "📦 Portable Package Created",
            f"Windows portable package created",
            {
                "Artifact": zip_path.name,
                "Version": ctx.semantic_version,
                "Size": f"{zip_path.stat().st_size // (1024*1024)} MB",
            },
            color=COLOR_GREEN,
        )

    def _create_portable_zip(self, ctx: Context) -> Path:
        """Create ZIP package of the entire Chromium directory."""
        chromium_dir = ctx.chromium_src

        # Create output directory
        output_dir = ctx.get_dist_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate ZIP filename: NexusOS_v0.37.0_x64.zip
        zip_name = f"NexusOS_v{ctx.semantic_version}_{ctx.architecture}.zip"
        zip_path = output_dir / zip_name

        log_info(f"Creating portable package: {zip_name}")
        log_info(f"Source: {chromium_dir}")

        try:
            file_count = 0
            total_size = 0

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from chromium_src directory
                for file_path in chromium_dir.rglob("*"):
                    if file_path.is_file():
                        # Get relative path for archive
                        arcname = file_path.relative_to(chromium_dir)

                        # Add to ZIP
                        zipf.write(file_path, arcname)

                        file_count += 1
                        total_size += file_path.stat().st_size

                        # Log progress every 100 files
                        if file_count % 100 == 0:
                            log_info(f"  Added {file_count} files ({total_size // (1024*1024)} MB)...")

            final_size = zip_path.stat().st_size
            log_info(f"Total files added: {file_count}")
            log_info(f"Uncompressed size: {total_size // (1024*1024)} MB")
            log_info(f"Compressed size: {final_size // (1024*1024)} MB")
            log_info(f"Compression ratio: {(1 - final_size/total_size)*100:.1f}%")

            log_success(f"Portable ZIP created: {zip_name}")
            return zip_path

        except Exception as e:
            raise RuntimeError(f"Failed to create portable ZIP: {e}")
