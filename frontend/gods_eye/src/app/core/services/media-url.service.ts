import { Injectable } from '@angular/core';
import { API_ORIGIN } from '../config/api.config';

/**
 * Builds absolute URLs for Django ``FileField`` / ``ImageField`` values and uploaded media paths.
 */
@Injectable({
  providedIn: 'root',
})
export class MediaUrlService {
  readonly origin = API_ORIGIN;

  /** Returns absolute URL for browser ``<img>`` / ``<video>`` ``src``. */
  mediaUrl(path: string | null | undefined): string {
    if (!path) {
      return '';
    }
    const raw = path.trim();
    if (raw.startsWith('http://') || raw.startsWith('https://')) {
      return raw;
    }
    let p = raw.startsWith('/') ? raw : `/${raw}`;
    if (!p.startsWith('/media/')) {
      p = `/media${p}`;
    }
    return `${API_ORIGIN}${p}`;
  }
}
