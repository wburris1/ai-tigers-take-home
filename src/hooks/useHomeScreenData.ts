import { useEffect, useMemo, useRef } from "react";
import { useTableData } from "./api/useTableData";

export function useHomeScreenData() {
  const {
    data,
    isPending,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useTableData();

  const scrollRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const columns = data?.pages[0]?.columns ?? [];
  const total = data?.pages[0]?.total ?? 0;
  const tableName = data?.pages[0]?.table;

  const flatRows = useMemo(
    () => data?.pages.flatMap((p) => p.rows) ?? [],
    [data?.pages],
  );

  useEffect(() => {
    const root = scrollRef.current;
    const sentinel = sentinelRef.current;
    if (!root || !sentinel || !hasNextPage) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries.some((e) => e.isIntersecting);
        if (hit && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage();
        }
      },
      { root, rootMargin: "120px", threshold: 0 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, data?.pages.length]);

  const hasTableData = Boolean(data && columns.length > 0);

  return {
    columns,
    total,
    tableName,
    flatRows,
    hasTableData,
    isPending,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    scrollRef,
    sentinelRef,
  };
}
