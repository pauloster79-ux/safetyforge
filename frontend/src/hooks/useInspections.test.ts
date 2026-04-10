import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useInspections, useInspection, useCreateInspection } from './useInspections'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects/:projectId/inspections`, ({ request }) => {
    const url = new URL(request.url)
    const type = url.searchParams.get('type')
    const inspections = [
      { id: 'insp_1', inspection_type: 'daily', overall_status: 'pass' },
      { id: 'insp_2', inspection_type: 'weekly', overall_status: 'fail' },
    ]
    const filtered = type ? inspections.filter(i => i.inspection_type === type) : inspections
    return HttpResponse.json({ inspections: filtered, total: filtered.length })
  }),
  http.get(`${BASE}/me/projects/:projectId/inspections/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, inspection_type: 'daily', overall_status: 'pass' }),
  ),
  http.post(`${BASE}/me/projects/:projectId/inspections`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { id: 'insp_new', inspection_type: body.inspection_type, overall_status: 'pass' },
      { status: 201 },
    )
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useInspections', () => {
  // [HAPPY] List inspections via nested project path
  it('fetches inspections from /me/projects/{id}/inspections and unwraps envelope', async () => {
    const { result } = renderHookWithClient(() => useInspections('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('insp_1')
  })

  // [EDGE] Disabled when projectId is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useInspections(undefined))
    expect(result.current.isFetching).toBe(false)
  })

  // [HAPPY] Passes type filter as query param
  it('passes type filter as query parameter', async () => {
    const { result } = renderHookWithClient(() => useInspections('proj_1', { type: 'daily' }))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].inspection_type).toBe('daily')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no inspections match', async () => {
    server.use(
      http.get(`${BASE}/me/projects/:projectId/inspections`, () =>
        HttpResponse.json({ inspections: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useInspections('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useInspection', () => {
  // [HAPPY] Fetches single inspection via nested path
  it('fetches from /me/projects/{pid}/inspections/{id}', async () => {
    const { result } = renderHookWithClient(() => useInspection('proj_1', 'insp_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.id).toBe('insp_1')
  })

  // [EDGE] Disabled when either ID is undefined
  it('does not fetch when projectId is undefined', () => {
    const { result } = renderHookWithClient(() => useInspection(undefined, 'insp_1'))
    expect(result.current.isFetching).toBe(false)
  })

  it('does not fetch when id is undefined', () => {
    const { result } = renderHookWithClient(() => useInspection('proj_1', undefined))
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateInspection', () => {
  // [HAPPY] Creates via nested project path without project_id in body
  it('POSTs to /me/projects/{pid}/inspections', async () => {
    let capturedBody: Record<string, unknown> | null = null
    server.use(
      http.post(`${BASE}/me/projects/:projectId/inspections`, async ({ request }) => {
        capturedBody = await request.json() as Record<string, unknown>
        return HttpResponse.json(
          { id: 'insp_new', inspection_type: 'daily', overall_status: 'pass' },
          { status: 201 },
        )
      }),
    )

    const { result } = renderHookWithClient(() => useCreateInspection('proj_1'))

    await result.current.mutateAsync({
      inspection_type: 'daily',
      inspection_date: '2026-04-03',
      inspector_name: 'Test',
      weather_conditions: 'sunny',
      temperature: '72',
      wind_conditions: 'calm',
      workers_on_site: 5,
      items: [],
      overall_notes: '',
      corrective_actions_needed: '',
      overall_status: 'pass',
    })

    expect(capturedBody).not.toBeNull()
    expect(capturedBody!.project_id).toBeUndefined()
    expect(capturedBody!.inspection_type).toBe('daily')
  })

  // [ERROR] 404 propagated
  it('propagates 404 errors', async () => {
    server.use(
      http.post(`${BASE}/me/projects/:projectId/inspections`, () =>
        HttpResponse.json({ detail: 'Project not found' }, { status: 404 }),
      ),
    )

    const { result } = renderHookWithClient(() => useCreateInspection('proj_bad'))

    await expect(
      result.current.mutateAsync({
        inspection_type: 'daily',
        inspection_date: '2026-04-03',
        inspector_name: 'Test',
        weather_conditions: 'sunny',
        temperature: '72',
        wind_conditions: 'calm',
        workers_on_site: 5,
        items: [],
        overall_notes: '',
        corrective_actions_needed: '',
        overall_status: 'pass',
      }),
    ).rejects.toThrow()
  })
})
