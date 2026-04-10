import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useHazardReports, useAnalyzePhoto } from './useHazardReports'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects/:projectId/hazard-reports`, ({ request }) => {
    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const reports = [
      { id: 'hr_1', description: 'Exposed wiring', status: 'open' },
      { id: 'hr_2', description: 'Missing guardrail', status: 'resolved' },
    ]
    const filtered = status ? reports.filter(r => r.status === status) : reports
    return HttpResponse.json({ reports: filtered, total: filtered.length })
  }),
  http.post(`${BASE}/me/analyze-photo`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({
      identified_hazards: [{ name: 'Exposed wiring', severity: 'high' }],
      hazard_count: 1,
      highest_severity: 'high',
      scene_description: 'Construction site with electrical hazards',
      positive_observations: ['Workers wearing PPE'],
      summary: 'One high-severity hazard found',
      photo_base64: body.photo_base64,
    })
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useHazardReports', () => {
  // [HAPPY] List from nested project path and unwrap envelope
  it('fetches from /me/projects/{pid}/hazard-reports and unwraps .reports', async () => {
    const { result } = renderHookWithClient(() => useHazardReports('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('hr_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useHazardReports(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no reports exist', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/hazard-reports`, () =>
        HttpResponse.json({ reports: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useHazardReports('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useAnalyzePhoto', () => {
  // [HAPPY] POSTs to /me/analyze-photo (NOT /me/hazard-reports/quick-analysis)
  it('POSTs to /me/analyze-photo', async () => {
    let capturedUrl = ''
    server.use(
      http.post(`${BASE}/me/analyze-photo`, ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          identified_hazards: [],
          hazard_count: 0,
          highest_severity: null,
          scene_description: 'Clean site',
          positive_observations: [],
          summary: 'No hazards found',
        })
      }),
    )

    const { result } = renderHookWithClient(() => useAnalyzePhoto())

    await result.current.mutateAsync({
      photo_base64: 'data:image/jpeg;base64,abc123',
    })

    expect(capturedUrl).toContain('/me/analyze-photo')
    expect(capturedUrl).not.toContain('/hazard-reports/')
  })

  // [ERROR] Server error propagated
  it('propagates error responses', async () => {
    server.use(
      http.post(`${BASE}/me/analyze-photo`, () =>
        HttpResponse.json({ detail: 'Analysis failed' }, { status: 500 }),
      ),
    )

    const { result } = renderHookWithClient(() => useAnalyzePhoto())

    await expect(
      result.current.mutateAsync({
        photo_base64: 'data:image/jpeg;base64,invalid',
      }),
    ).rejects.toThrow()
  })
})
