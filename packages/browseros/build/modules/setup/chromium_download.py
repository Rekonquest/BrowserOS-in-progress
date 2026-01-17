#!/usr/bin/env python3
"""
Download pre-built Chromium binaries instead of compiling from source.

This module replaces the traditional git_setup + compile workflow with
a binary download approach similar to Brave, Vivaldi, and Edge browsers.

Instead of:
  git_setup → compile (4-8 hours, 100+ GB)

We do:
  chromium_download (5-10 minutes, ~500 MB)
"""

from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

from build.common.context import Context
from build.common.exceptions import ValidationError, ExecutionError
from build.common.module import CommandModule
from build.common.platform import IS_WINDOWS, IS_MACOS, IS_LINUX
from build.common.utils import log_info, log_success, log_error, log_warning

# Public Chromium snapshot repositories
# These provide official, pre-built Chromium binaries for all platforms
CHROMIUM_SNAPSHOT_BASE_URLS = {
    "official": "https://commondatastorage.googleapis.com/chromium-browser-snapshots",
    "ungoogled": "https://github.com/ungoogled-software/ungoogled-chromium/releases/download",
}


class ChromiumDownloadModule(CommandModule):
    """
    Download pre-built Chromium binaries for the target platform.

    This module:
    1. Determines platform-specific download URL
    2. Downloads Chromium binary archive
    3. Extracts to chromium_src directory
    4. Validates the extracted binary

    Configuration:
        Set CHROMIUM_BINARY_SOURCE environment variable:
        - "official" (default): Google's official Chromium snapshots
        - "ungoogled": Ungoogled Chromium releases
        - "r2": Custom binaries from your R2 storage
        - "local": Use local file (for testing)

    Example usage:
        # Download official Chromium
        browseros build --modules chromium_download,resources,package_linux

        # Use custom R2-hosted binaries
        export CHROMIUM_BINARY_SOURCE=r2
        browseros build --modules chromium_download,resources,package_linux
    """

    name = "chromium_download"
    description = "Download pre-built Chromium binaries"

    def validate(self, context: Context) -> None:
        """Validate that we have required configuration for binary downloads."""
        if not context.chromium_version:
            raise ValidationError(
                "chromium_version is required for binary downloads. "
                "Set via CHROMIUM_VERSION env var or config."
            )

        if not context.chromium_src:
            raise ValidationError(
                "chromium_src directory must be specified. "
                "Set via --chromium-src or CHROMIUM_SRC env var."
            )

        # Validate binary source
        binary_source = context.env.chromium_binary_source or "official"
        if binary_source not in ["official", "ungoogled", "r2", "local"]:
            raise ValidationError(
                f"Invalid CHROMIUM_BINARY_SOURCE: {binary_source}. "
                "Must be one of: official, ungoogled, r2, local"
            )

    def execute(self, context: Context) -> bool:
        """Download and extract Chromium binary for the target platform."""
        log_info("=" * 70)
        log_info("Chromium Binary Download")
        log_info("=" * 70)

        binary_source = context.env.chromium_binary_source or "official"
        log_info(f"Binary source: {binary_source}")
        log_info(f"Chromium version: {context.chromium_version}")

        # Determine platform
        if IS_WINDOWS():
            platform_name = "windows"
        elif IS_MACOS():
            platform_name = "macos"
        elif IS_LINUX():
            platform_name = "linux"
        else:
            raise ExecutionError("Unsupported platform")

        log_info(f"Platform: {platform_name}")
        log_info(f"Architecture: {context.architecture}")

        # Prepare chromium_src directory
        self._prepare_chromium_directory(context)

        # Download based on source
        if binary_source == "official":
            archive_path = self._download_official_chromium(context, platform_name)
        elif binary_source == "ungoogled":
            archive_path = self._download_ungoogled_chromium(context, platform_name)
        elif binary_source == "r2":
            archive_path = self._download_r2_chromium(context, platform_name)
        elif binary_source == "local":
            archive_path = self._use_local_chromium(context)
        else:
            raise ExecutionError(f"Unsupported binary source: {binary_source}")

        # Extract archive
        self._extract_archive(archive_path, context)

        # Validate extracted binary
        self._validate_chromium_binary(context)

        log_success("✅ Chromium binary download complete!")
        return True

    def _prepare_chromium_directory(self, context: Context) -> None:
        """Prepare the chromium_src directory for binary extraction."""
        chromium_dir = context.chromium_src

        if chromium_dir.exists():
            log_warning(f"Chromium directory exists: {chromium_dir}")
            log_info("Clearing existing directory...")
            shutil.rmtree(chromium_dir)

        chromium_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Created: {chromium_dir}")

    def _download_official_chromium(self, context: Context, platform_name: str) -> Path:
        """
        Download from Google's official Chromium snapshot repository.

        URL pattern:
        https://commondatastorage.googleapis.com/chromium-browser-snapshots/
          {platform}/{build_number}/chrome-{platform}.zip
        """
        log_info("Downloading from official Chromium snapshots...")

        # Map platform to snapshot URL format
        platform_map = {
            ("windows", "x64"): ("Win_x64", "chrome-win.zip"),
            ("macos", "x64"): ("Mac", "chrome-mac.zip"),
            ("macos", "arm64"): ("Mac_Arm", "chrome-mac.zip"),
            ("linux", "x64"): ("Linux_x64", "chrome-linux.zip"),
        }

        platform_key = (platform_name, context.architecture)
        if platform_key not in platform_map:
            raise ExecutionError(
                f"Unsupported platform/arch for official Chromium: {platform_key}"
            )

        platform_dir, archive_name = platform_map[platform_key]

        # Get latest build number for the platform
        base_url = CHROMIUM_SNAPSHOT_BASE_URLS["official"]
        latest_url = f"{base_url}/{platform_dir}/LATEST"

        log_info(f"Fetching latest build number from: {latest_url}")

        try:
            import requests
            response = requests.get(latest_url, timeout=30)
            response.raise_for_status()
            build_number = response.text.strip()
            log_success(f"Latest build number: {build_number}")
        except Exception as e:
            log_error(f"Failed to fetch latest build number: {e}")
            log_warning("Falling back to recent known build: 1400000")
            build_number = "1400000"

        download_url = f"{base_url}/{platform_dir}/{build_number}/{archive_name}"
        log_info(f"Download URL: {download_url}")

        # Download to temporary location
        temp_dir = context.root_dir / "build" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        archive_path = temp_dir / archive_name

        # Download the archive
        log_info(f"Downloading Chromium... (this may take a few minutes)")
        try:
            import requests
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(archive_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (10 * 1024 * 1024) < 8192:  # Log every 10MB
                                log_info(f"  Downloaded: {downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB ({percent:.1f}%)")

            log_success(f"Download complete: {archive_path.name}")
        except Exception as e:
            raise ExecutionError(
                f"Failed to download Chromium: {e}\n\n"
                "Alternative options:\n"
                "1. Set CHROMIUM_BINARY_SOURCE=local and provide local archive\n"
                "2. Set CHROMIUM_BINARY_SOURCE=r2 and upload to your R2 bucket\n"
                "3. Manually download from: {download_url}"
            )

        return archive_path

    def _download_ungoogled_chromium(self, context: Context, platform_name: str) -> Path:
        """Download from Ungoogled Chromium releases."""
        log_info("Downloading from Ungoogled Chromium releases...")
        raise NotImplementedError(
            "Ungoogled Chromium download not yet implemented. "
            "Use CHROMIUM_BINARY_SOURCE=r2 for custom binaries."
        )

    def _download_r2_chromium(self, context: Context, platform_name: str) -> Path:
        """
        Download from custom R2 storage.

        This is the recommended approach for NexusOS since you control
        the binaries and can upload your own pre-built Chromium versions.
        """
        log_info("Downloading from R2 storage...")

        # Import R2 utilities
        from build.modules.storage.r2 import get_r2_client, download_file_from_r2

        # R2 key pattern
        platform_arch = f"{platform_name}-{context.architecture}"
        r2_key = f"binaries/chromium/chromium-{context.chromium_version}-{platform_arch}.tar.xz"

        log_info(f"R2 key: {r2_key}")

        # Download to temp directory
        temp_dir = context.root_dir / "build" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        archive_path = temp_dir / f"chromium-{platform_arch}.tar.xz"

        # Get R2 client and download
        bucket = context.env.r2_bucket_name or "nexusos-binaries"
        client = get_r2_client(context.env)

        success = download_file_from_r2(client, r2_key, archive_path, bucket)

        if not success:
            raise ExecutionError(
                f"Failed to download Chromium binary from R2: {r2_key}\n\n"
                "Make sure you've uploaded pre-built Chromium binaries to R2.\n"
                "See BINARY_DOWNLOAD_GUIDE.md for instructions."
            )

        return archive_path

    def _use_local_chromium(self, context: Context) -> Path:
        """Use local Chromium binary archive for testing."""
        log_info("Using local Chromium binary...")

        local_path = context.env.chromium_binary_path
        if not local_path:
            raise ExecutionError(
                "CHROMIUM_BINARY_PATH environment variable required when using "
                "CHROMIUM_BINARY_SOURCE=local"
            )

        archive_path = Path(local_path)
        if not archive_path.exists():
            raise ExecutionError(f"Local Chromium binary not found: {archive_path}")

        log_info(f"Using: {archive_path}")
        return archive_path

    def _extract_archive(self, archive_path: Path, context: Context) -> None:
        """Extract Chromium binary archive to chromium_src directory."""
        log_info(f"Extracting: {archive_path.name}")

        if not archive_path.exists():
            log_warning(f"Archive not found (stub mode): {archive_path}")
            log_warning("Skipping extraction. See BINARY_DOWNLOAD_GUIDE.md")
            return

        chromium_dir = context.chromium_src

        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(chromium_dir)
                log_success(f"Extracted ZIP to: {chromium_dir}")

        elif archive_path.suffix in [".xz", ".gz", ".bz2"] or ".tar" in archive_path.name:
            with tarfile.open(archive_path, "r:*") as tar_ref:
                tar_ref.extractall(chromium_dir)
                log_success(f"Extracted TAR to: {chromium_dir}")

        else:
            raise ExecutionError(
                f"Unsupported archive format: {archive_path.suffix}\n"
                "Supported: .zip, .tar.gz, .tar.xz, .tar.bz2"
            )

        # Clean up archive
        archive_path.unlink()
        log_info("Cleaned up archive file")

    def _validate_chromium_binary(self, context: Context) -> None:
        """Validate that the extracted Chromium binary is functional."""
        log_info("Validating Chromium binary...")

        chromium_dir = context.chromium_src
        if not chromium_dir.exists():
            log_warning("⚠️  Chromium directory not found (stub mode)")
            return

        # Check for key files/directories
        expected_files = []

        if IS_WINDOWS():
            expected_files = ["chrome.exe", "chrome.dll"]
        elif IS_MACOS():
            expected_files = ["Chromium.app"]
        elif IS_LINUX():
            expected_files = ["chrome", "chrome_sandbox"]

        missing_files = []
        for file_name in expected_files:
            if not (chromium_dir / file_name).exists():
                missing_files.append(file_name)

        if missing_files:
            raise ExecutionError(
                f"Chromium binary validation failed. Missing files:\n"
                + "\n".join(f"  - {f}" for f in missing_files)
            )

        log_success("✓ Chromium binary validation passed")


# Register module
__all__ = ["ChromiumDownloadModule"]
