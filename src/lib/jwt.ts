function base64UrlToUtf8(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const pad = base64.length % 4;
  const padded = pad ? base64 + "=".repeat(4 - pad) : base64;
  return atob(padded);
}

export type JwtPayload = {
  sub?: string;
  name?: string;
  exp?: number;
  iat?: number;
};

/** Decode JWT payload for display only; does not verify the signature. */
export function decodeJwtPayload(token: string): JwtPayload | null {
  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }
  try {
    const json = base64UrlToUtf8(parts[1]);
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}
