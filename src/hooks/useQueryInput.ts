import { useCallback, useState, type ChangeEvent } from "react";

export function useQueryInput() {
  const [query, setQuery] = useState("");

  const onQueryChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  return {
    query,
    onQueryChange,
  };
}
