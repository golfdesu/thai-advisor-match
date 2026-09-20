export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

/**
 * Returns a consistent fallback avatar URL using the Coral Orange brand palette.
 */
export function getAdvisorAvatarUrl(name?: string): string {
  const cleanName = encodeURIComponent(name || "Faculty");
  return `https://ui-avatars.com/api/?name=${cleanName}&background=FF7A59&color=24110C`;
}
