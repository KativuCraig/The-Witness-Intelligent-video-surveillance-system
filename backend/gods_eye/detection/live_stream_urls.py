"""Resolve common «IP Camera» iOS/Android (ShenYao) home URLs to MJPEG stream candidates."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def live_http_candidate_urls(stream_url: str) -> list[str]:
    raw = (stream_url or "").strip()
    if not raw:
        return []
    p = urlparse(raw)
    if p.scheme not in ("http", "https"):
        return [raw]

    path = (p.path or "/").rstrip("/") or "/"
    has_real_path = path != "/"

    ordered: list[str] = []
    seen: set[str] = set()

    def add(u: str) -> None:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            ordered.append(u)

    add(raw)

    if not has_real_path and not p.query:
        origin = urlunparse((p.scheme, p.netloc, "", "", "", ""))
        for suffix in ("/video", "/videofeed", "/video.mjpg", "/mjpeg"):
            add(origin + suffix)

    return ordered
