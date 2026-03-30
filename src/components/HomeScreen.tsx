import { useHomeScreenData } from "../hooks/useHomeScreenData";

type HomeScreenProps = {
  displayName: string;
  onLogout: () => void;
};

export function HomeScreen({ displayName, onLogout }: HomeScreenProps) {
  const {
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
  } = useHomeScreenData();

  return (
    <div className="app">
      <header>
        <h1>AI Tigers Take Home</h1>
        <p>Signed in as {displayName}</p>
      </header>
      <button type="button" onClick={onLogout}>
        Log out
      </button>

      <section className="data-section" aria-label="Dataset preview">
        {isPending && <p>Loading data…</p>}
        {isError && (
          <p role="alert">
            {error instanceof Error ? error.message : "Could not load data."}
          </p>
        )}
        {hasTableData && (
          <>
            <p className="data-meta">
              Table: <code>{tableName}</code> — showing {flatRows.length} of{" "}
              {total} row{total === 1 ? "" : "s"}
            </p>
            <div className="data-table-wrap" ref={scrollRef}>
              <table className="data-table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col} scope="col">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {flatRows.map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci}>
                          {cell === null ? "" : String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {hasNextPage && (
                <div
                  ref={sentinelRef}
                  className="data-table-sentinel"
                  aria-hidden
                />
              )}
              {isFetchingNextPage && (
                <p className="data-table-loading">Loading more…</p>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
