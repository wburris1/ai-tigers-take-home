import { useCallback, useState, type ChangeEvent } from "react";
import { useAIQuery } from "./api/useAIQuery";

export function useQueryInput() {
  const [query, setQuery] = useState("");
  const { mutate, data, isPending, isError, error } = useAIQuery();

  const onQueryChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  const onSubmit = useCallback(() => {
    mutate({ query });
  }, [mutate, query]);

  return {
    query,
    onQueryChange,
    onSubmit,
    aiResult: data,
    isAiPending: isPending,
    isAiError: isError,
    aiError: error,
  };
}
