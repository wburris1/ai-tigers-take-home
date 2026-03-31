import { useQueryInput } from "../hooks/useQueryInput";
import { useHomeScreenData } from "../hooks/useTable";

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

  const {
    query,
    onQueryChange,
    onSubmit,
    aiResult,
    isAiPending,
    isAiError,
    aiError,
  } = useQueryInput();

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
            <div className="data-section-query">
              <label htmlFor="home-screen-query">Query</label>
              <input
                id="home-screen-query"
                name="query"
                type="text"
                value={query}
                onChange={onQueryChange}
                autoComplete="off"
              />
              <button
                type="button"
                onClick={onSubmit}
                disabled={isAiPending || !query.trim()}
              >
                {isAiPending ? "Sending…" : "Submit"}
              </button>
              {isAiPending && <p className="ai-query-status">Thinking…</p>}
              {isAiError && (
                <p className="ai-query-error" role="alert">
                  {aiError instanceof Error
                    ? aiError.message
                    : "AI request failed."}
                </p>
              )}
              {aiResult && (
                <div className="ai-query-result" aria-live="polite">
                  <p className="ai-query-result-meta">
                    Model: <code>{aiResult.model}</code>
                  </p>
                  {aiResult.sql && (
                    <p className="ai-query-result-meta">
                      SQL:{" "}
                      <code className="ai-query-result-sql">{aiResult.sql}</code>
                    </p>
                  )}
                  <pre className="ai-query-result-text">{aiResult.text}</pre>
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
