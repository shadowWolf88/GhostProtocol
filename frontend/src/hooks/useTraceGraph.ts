import { useQuery } from '@tanstack/react-query'
import { traceApi } from '../services/api'

export function useTraceGraph() {
  return useQuery({
    queryKey: ['traceGraph'],
    queryFn: () => traceApi.getGraph(),
    refetchInterval: 30_000,
    staleTime: 20_000,
  })
}
