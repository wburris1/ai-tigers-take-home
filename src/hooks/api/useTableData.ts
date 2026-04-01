import { useInfiniteQuery } from "@tanstack/react-query";
import { getStoredToken, invalidateSession } from "../../lib/session";

/** Rows fetched per request; must match default `limit` on GET /api/data. */
export const TABLE_PAGE_SIZE = 50;

export type TableDataPage = {
  table: string;
  columns: string[];
  rows: (string | number | boolean | null)[][];
  total: number;
  offset: number;
  limit: number;
};

async function fetchTablePage(offset: number): Promise<TableDataPage> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Not authenticated");
  }
  const params = new URLSearchParams({
    limit: String(TABLE_PAGE_SIZE),
    offset: String(offset),
  });
  const res = await fetch(`/api/data?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    invalidateSession();
    throw new Error("Session expired. Log in again.");
  }
  if (!res.ok) {
    let message = "Failed to load data";
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data.detail === "string") {
        message = data.detail;
      }
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json() as Promise<TableDataPage>;
}

export function useTableData() {
  return useInfiniteQuery({
    queryKey: ["tableData", TABLE_PAGE_SIZE],
    queryFn: ({ pageParam }) => fetchTablePage(pageParam as number),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.offset + lastPage.rows.length;
      return nextOffset < lastPage.total ? nextOffset : undefined;
    },
    retry: false,
  });
}
