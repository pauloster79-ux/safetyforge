import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useMorningBrief, useMorningBriefHistory } from './useMorningBrief'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects/:projectId/morning-brief`, () =>
    HttpResponse.json({
      id: 'mb_1',
      project_id: 'proj_1',
      date: '2026-04-03',
      weather: { temperature: 72, conditions: 'sunny' },
      safety_focus: 'Heat stress prevention',
      tasks: ['Foundation pour', 'Framing'],
    }),
  ),
  http.get(`${BASE}/me/projects/:projectId/morning-briefs`, () =>
    HttpResponse.json({
      briefs: [
        { id: 'mb_1', date: '2026-04-03', safety_focus: 'Heat stress prevention' },
        { id: 'mb_2', date: '2026-04-02', safety_focus: 'Fall protection' },
      ],
      total: 2,
    }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useMorningBrief', () => {
  // [HAPPY] Fetches from /me/projects/{pid}/morning-brief (singular, no /today)
  it('fetches from /me/projects/{pid}/morning-brief (singular path)', async () => {
    const { result } = renderHookWithClient(() => useMorningBrief('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.id).toBe('mb_1')
    expect(result.current.data!.safety_focus).toBe('Heat stress prevention')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useMorningBrief(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [ERROR] 404 when no brief exists
  it('handles 404 when no brief exists for today', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/morning-brief`, () =>
        HttpResponse.json({ detail: 'No brief for today' }, { status: 404 }),
      ),
    )

    const { result } = renderHookWithClient(() => useMorningBrief('proj_1'))

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useMorningBriefHistory', () => {
  // [HAPPY] Fetches from plural path and unwraps .briefs
  it('fetches from /me/projects/{pid}/morning-briefs and unwraps .briefs', async () => {
    const { result } = renderHookWithClient(() => useMorningBriefHistory('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('mb_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useMorningBriefHistory(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no history exists', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/morning-briefs`, () =>
        HttpResponse.json({ briefs: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useMorningBriefHistory('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})
