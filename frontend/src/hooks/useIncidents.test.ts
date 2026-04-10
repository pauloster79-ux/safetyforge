import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useIncidents, useInvestigateIncident } from './useIncidents'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects/:projectId/incidents`, () =>
    HttpResponse.json({
      incidents: [
        { id: 'inc_1', description: 'Slip and fall', severity: 'minor', status: 'reported' },
        { id: 'inc_2', description: 'Equipment failure', severity: 'major', status: 'investigating' },
      ],
      total: 2,
    }),
  ),
  http.post(`${BASE}/me/projects/:projectId/incidents/:id/investigate`, ({ params }) =>
    HttpResponse.json({
      id: params.id,
      description: 'Slip and fall',
      severity: 'minor',
      status: 'investigating',
      ai_analysis: { root_cause: 'Wet floor', recommendations: ['Install drainage'] },
    }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useIncidents', () => {
  // [HAPPY] List from nested project path and unwrap envelope
  it('fetches from /me/projects/{pid}/incidents and unwraps .incidents', async () => {
    const { result } = renderHookWithClient(() => useIncidents('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('inc_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useIncidents(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no incidents exist', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/incidents`, () =>
        HttpResponse.json({ incidents: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useIncidents('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useInvestigateIncident', () => {
  // [HAPPY] POSTs to /me/projects/{pid}/incidents/{id}/investigate
  it('POSTs to the investigate endpoint', async () => {
    let capturedUrl = ''
    server.use(
      http.post(`${BASE}/me/projects/:projectId/incidents/:id/investigate`, ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          id: 'inc_1',
          description: 'Slip and fall',
          severity: 'minor',
          status: 'investigating',
          ai_analysis: { root_cause: 'Wet floor' },
        })
      }),
    )

    const { result } = renderHookWithClient(() => useInvestigateIncident('proj_1'))

    await result.current.mutateAsync('inc_1')

    expect(capturedUrl).toContain('/me/projects/proj_1/incidents/inc_1/investigate')
  })

  // [ERROR] 404 propagated
  it('propagates error responses', async () => {
    server.use(
      http.post(`${BASE}/me/projects/:projectId/incidents/:id/investigate`, () =>
        HttpResponse.json({ detail: 'Incident not found' }, { status: 404 }),
      ),
    )

    const { result } = renderHookWithClient(() => useInvestigateIncident('proj_1'))

    await expect(result.current.mutateAsync('inc_bad')).rejects.toThrow()
  })
})
