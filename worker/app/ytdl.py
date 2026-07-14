"""yt-dlp wrapper. Returns metadata + the final file path."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp


@dataclass
class DownloadResult:
    file_path: Path
    title: str
    thumbnail: str | None
    duration: int | None
    ext: str


def _format_selector(media_type: str, quality: str) -> str:
    if media_type == "audio" or quality == "audio":
        return "bestaudio/best"
    # Many videos no longer offer a muxed mp4/m4a pair at all (YouTube has
    # been shifting non-premium formats to AV1/VP9-in-webm-only). The old
    # chain ended at a bare "best", which still failed on videos where the
    # *only* available streams are separate video-only + audio-only tracks
    # in non-mp4/m4a containers. `bv*+ba/b` is yt-dlp's own unconstrained
    # catch-all (any video+any audio, else any single format) — ffmpeg
    # remuxes/merges to mp4 via merge_output_format regardless of source
    # container, so this never sacrifices the final output format.
    if quality == "1080p":
        return (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]"
            "/best[height<=1080]"
            "/bestvideo[height<=1080]+bestaudio"
            "/bv*+ba/b"
        )
    if quality == "720p":
        return (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
            "/best[height<=720]"
            "/bestvideo[height<=720]+bestaudio"
            "/bv*+ba/b"
        )
    # best
    return (
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
        "/best[ext=mp4]"
        "/bestvideo+bestaudio"
        "/bv*+ba/b"
    )


def run_ytdlp(
    url: str,
    media_type: str,
    quality: str,
    out_dir: Path,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    cookies_file: str | None = None,
    proxy: str | None = None,
) -> DownloadResult:
    out_dir.mkdir(parents=True, exist_ok=True)

    def hook(d: dict[str, Any]) -> None:
        if on_progress:
            on_progress(d)

    ydl_opts: dict[str, Any] = {
        "format": _format_selector(media_type, quality),
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": True,
        "progress_hooks": [hook],
        "merge_output_format": "mp4",
        "restrictfilenames": True,
        "retries": 3,
    }

    # YouTube's "Sign in to confirm you're not a bot" wall — export a
    # Netscape-format cookies.txt from a logged-in browser session and mount
    # it into the worker (see README § YouTube bot-check). Silently skipped
    # if unset/missing so a bad path never breaks non-YouTube downloads.
    if cookies_file and Path(cookies_file).is_file():
        ydl_opts["cookiefile"] = cookies_file

    # Route the download through a proxy (e.g. a SOCKS5 tunnel back to a
    # residential/home network) instead of this container's own egress IP —
    # datacenter IP ranges get bot-walled far more aggressively than
    # residential ones, independent of cookies. socks5:// requires PySocks
    # (see requirements.txt); yt-dlp raises a clear error if it's missing.
    if proxy:
        ydl_opts["proxy"] = proxy

    if media_type == "audio":
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ]
    else:
        ydl_opts["postprocessors"] = [
            {"key": "FFmpegMetadata"},
        ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # After post-processing, the actual filename may differ; resolve it
        requested = ydl.prepare_filename(info)
        final = Path(requested)
        if media_type == "audio":
            final = final.with_suffix(".mp3")
        elif final.suffix != ".mp4":
            mp4 = final.with_suffix(".mp4")
            if mp4.exists():
                final = mp4

        # Pick a thumbnail from disk if yt-dlp wrote one
        thumb_url = info.get("thumbnail")
        for ext in (".jpg", ".webp", ".png"):
            t = final.with_suffix(ext)
            if t.exists():
                # use remote thumbnail URL for the DB row (smaller); local file is auxiliary
                break

        return DownloadResult(
            file_path=final,
            title=info.get("title") or "Untitled",
            thumbnail=thumb_url,
            duration=int(info["duration"]) if info.get("duration") else None,
            ext=final.suffix.lstrip("."),
        )


def cleanup(out_dir: Path) -> None:
    """Remove all files in a working directory, then the dir itself."""
    if not out_dir.exists():
        return
    for p in out_dir.glob("**/*"):
        try:
            if p.is_file():
                p.unlink()
        except OSError:
            pass
    try:
        out_dir.rmdir()
    except OSError:
        pass
