/** Normalize Django REST list responses (array or `{ results: [...] }`). */
export function unwrapList<T>(body: T[] | { results?: T[] }): T[] {
  if (Array.isArray(body)) {
    return body;
  }
  if (body && typeof body === 'object' && Array.isArray(body.results)) {
    return body.results;
  }
  return [];
}
