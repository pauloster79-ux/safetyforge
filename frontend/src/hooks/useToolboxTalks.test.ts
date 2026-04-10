import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import {
  useToolboxTalks,
  useToolboxTalk,
  useCreateToolboxTalk,
  useAddAttendee,
  useCompleteTalk,
} from './useToolboxTalks'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects/:projectId/toolbox-talks`, ({ request }) => {
    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const talks = [
      { id: 'tt_1', topic: 'Fall Protection', status: 'scheduled' },
      { id: 'tt_2', topic: 'Heat Stress', status: 'completed' },
    ]
    const filtered = status ? talks.filter(t => t.status === status) : talks
    return HttpResponse.json({ toolbox_talks: filtered, total: filtered.length })
  }),
  http.get(`${BASE}/me/projects/:projectId/toolbox-talks/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, topic: 'Fall Protection', status: 'scheduled' }),
  ),
  http.post(`${BASE}/me/projects/:projectId/toolbox-talks`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { id: 'tt_new', topic: body.topic, status: 'scheduled' },
      { status: 201 },
    )
  }),
  http.post(`${BASE}/me/projects/:projectId/toolbox-talks/:id/attend`, async ({ request, params }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({
      id: params.id,
      topic: 'Fall Protection',
      status: 'in_progress',
      attendees: [{ worker_name: body.worker_name }],
    })
  }),
  http.post(`${BASE}/me/projects/:projectId/toolbox-talks/:id/complete`, ({ params }) =>
    HttpResponse.json({ id: params.id, topic: 'Fall Protection', status: 'completed' }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useToolboxTalks', () => {
  // [HAPPY] List from nested project path and unwrap envelope
  it('fetches from /me/projects/{pid}/toolbox-talks and unwraps .toolbox_talks', async () => {
    const { result } = renderHookWithClient(() => useToolboxTalks('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('tt_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useToolboxTalks(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no talks exist', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/toolbox-talks`, () =>
        HttpResponse.json({ toolbox_talks: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useToolboxTalks('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useToolboxTalk', () => {
  // [HAPPY] Fetches single talk from nested path
  it('fetches from /me/projects/{pid}/toolbox-talks/{id}', async () => {
    const { result } = renderHookWithClient(() => useToolboxTalk('proj_1', 'tt_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.id).toBe('tt_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useToolboxTalk(undefined, 'tt_1'))
    expect(result.current.isFetching).toBe(false)
  })

  // [EDGE] Disabled when id is undefined
  it('does not fetch when id is undefined', () => {
    const { result } = renderHookWithClient(() => useToolboxTalk('proj_1', undefined))
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateToolboxTalk', () => {
  // [HAPPY] POSTs to nested project path
  it('POSTs to /me/projects/{pid}/toolbox-talks', async () => {
    let capturedBody: Record<string, unknown> | null = null
    server.use(
      http.post(`${BASE}/me/projects/:projectId/toolbox-talks`, async ({ request }) => {
        capturedBody = await request.json() as Record<string, unknown>
        return HttpResponse.json(
          { id: 'tt_new', topic: 'Scaffolding Safety', status: 'scheduled' },
          { status: 201 },
        )
      }),
    )

    const { result } = renderHookWithClient(() => useCreateToolboxTalk('proj_1'))

    await result.current.mutateAsync({
      topic: 'Scaffolding Safety',
      target_audience: 'all',
      duration_minutes: 15,
    })

    expect(capturedBody).not.toBeNull()
    expect(capturedBody!.topic).toBe('Scaffolding Safety')
  })

  // [ERROR] 404 propagated
  it('propagates error responses', async () => {
    server.use(
      http.post(`${BASE}/me/projects/:projectId/toolbox-talks`, () =>
        HttpResponse.json({ detail: 'Project not found' }, { status: 404 }),
      ),
    )

    const { result } = renderHookWithClient(() => useCreateToolboxTalk('proj_bad'))

    await expect(
      result.current.mutateAsync({
        topic: 'Test',
        target_audience: 'all',
        duration_minutes: 10,
      }),
    ).rejects.toThrow()
  })
})

describe('useAddAttendee', () => {
  // [HAPPY] POSTs to attend nested path
  it('POSTs to /me/projects/{pid}/toolbox-talks/{id}/attend', async () => {
    let capturedUrl = ''
    server.use(
      http.post(`${BASE}/me/projects/:projectId/toolbox-talks/:id/attend`, async ({ request }) => {
        capturedUrl = request.url
        const body = await request.json() as Record<string, unknown>
        return HttpResponse.json({
          id: 'tt_1',
          topic: 'Fall Protection',
          status: 'in_progress',
          attendees: [{ worker_name: body.worker_name }],
        })
      }),
    )

    const { result } = renderHookWithClient(() => useAddAttendee('proj_1'))

    await result.current.mutateAsync({
      id: 'tt_1',
      worker_name: 'John Doe',
      language_preference: 'en',
    })

    expect(capturedUrl).toContain('/me/projects/proj_1/toolbox-talks/tt_1/attend')
  })
})

describe('useCompleteTalk', () => {
  // [HAPPY] POSTs to complete nested path
  it('POSTs to /me/projects/{pid}/toolbox-talks/{id}/complete', async () => {
    let capturedUrl = ''
    server.use(
      http.post(`${BASE}/me/projects/:projectId/toolbox-talks/:id/complete`, ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({ id: 'tt_1', topic: 'Fall Protection', status: 'completed' })
      }),
    )

    const { result } = renderHookWithClient(() => useCompleteTalk('proj_1'))

    await result.current.mutateAsync('tt_1')

    expect(capturedUrl).toContain('/me/projects/proj_1/toolbox-talks/tt_1/complete')
  })
})
