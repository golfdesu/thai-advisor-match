export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

/**
 * Returns a consistent fallback avatar URL using the brand palette (#5B0F18).
 */
export function getAdvisorAvatarUrl(name?: string): string {
  const cleanName = encodeURIComponent(name || "Faculty");
  return `https://ui-avatars.com/api/?name=${cleanName}&background=5B0F18&color=ffffff`;
}
