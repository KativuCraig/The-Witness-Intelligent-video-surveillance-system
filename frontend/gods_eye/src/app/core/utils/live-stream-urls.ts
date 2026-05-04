/**
 * 《IP Camera》/ IP Camera for iOS (ShenYao) and similar apps often show a *home* URL
 * like `http://192.168.1.5:8081/` while the actual MJPEG stream is on a subpath.
 * Browsers and OpenCV need the MJPEG URL, not the HTML landing page.
 */
export function liveHttpCandidateUrls(streamUrl: string): string[] {
  const raw = streamUrl.trim();
  if (!raw) {
    return [];
  }
  if (!/^https?:\/\//i.test(raw)) {
    return [raw];
  }
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    return [raw];
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return [raw];
  }

  const path = (parsed.pathname || '/').replace(/\/+$/, '') || '/';
  const hasRealPath = path !== '/' && path.length > 1;

  const origin = `${parsed.protocol}//${parsed.host}`;

  const ordered = new Set<string>();
  ordered.add(raw);

  if (!hasRealPath && !parsed.search) {
    // ShenYao IP Camera (iOS/Android) common MJPEG paths — try after exact URL fails
    const suffixes = ['/video', '/videofeed', '/video.mjpg', '/mjpeg', '/?action=stream'];
    for (const s of suffixes) {
      ordered.add(`${origin}${s}`);
    }
  }

  return [...ordered];
}
