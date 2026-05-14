import { useQuery } from "@tanstack/react-query";

import { loadModels, loadProviders } from "./api";
import type { Provider } from "./types";

export function useModels({ enabled = true }: { enabled?: boolean } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["models"],
    queryFn: () => loadModels(),
    enabled,
    refetchOnWindowFocus: false,
  });
  return { models: data ?? [], isLoading, error };
}

export function useProviders({ enabled = true }: { enabled?: boolean } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["providers"],
    queryFn: () => loadProviders(),
    enabled,
    refetchOnWindowFocus: false,
  });
  return { providers: data ?? [], isLoading, error };
}
