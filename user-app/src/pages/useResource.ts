import { useEffect, useState } from "react";

interface ResourceOptions<T> {
  enabled?: boolean;
  disabledValue?: T;
}

export function useResource<T>(loader: () => Promise<T>, deps: React.DependencyList = [], options: ResourceOptions<T> = {}) {
  const enabled = options.enabled ?? true;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    if (!enabled) {
      setData(options.disabledValue ?? null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await loader());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, [enabled, ...deps]);

  return { data, loading, error, reload };
}
