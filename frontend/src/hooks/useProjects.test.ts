import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useProjects, useProject, useCreateProject } from './useProjects'

const BASE = 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/projects`, ({ request }) => {
    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const projects = [
      { id: 'proj_1', name: 'Highway Bridge', status: 'active' },
      { id: 'proj_2', name: 'Office Tower', status: 'completed' },
    ]
    const filtered = status ? projects.filter(p => p.status === status) : projects
    return HttpResponse.json({ projects: filtered, total: filtered.length })
  }),
  http.get(`${BASE}/me/projects/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, name: 'Highway Bridge', status: 'active' }),
  ),
  http.post(`${BASE}/me/projects`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { id: 'proj_new', name: body.name, status: 'active' },
      { status: 201 },
    )
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useProjects', () => {
  // [HAPPY] List projects and unwrap envelope
  it('fetches projects from /me/projects and unwraps envelope', async () => {
    const { result } = renderHookWithClient(() => useProjects())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('proj_1')
  })

  // [HAPPY] Status filter passed as query param
  it('passes status filter as query parameter', async () => {
    const { result } = renderHookWithClient(() => useProjects({ status: 'active' }))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].status).toBe('active')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no projects match', async () => {
    server.use(
      http.get(`${BASE}/me/projects`, () =>
        HttpResponse.json({ projects: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useProjects())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useProject', () => {
  // [HAPPY] Fetches single project
  it('fetches single project from /me/projects/{id}', async () => {
    const { result } = renderHookWithClient(() => useProject('proj_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.id).toBe('proj_1')
  })

  // [EDGE] Disabled when id is undefined
  it('does not fetch when id is undefined', () => {
    const { result } = renderHookWithClient(() => useProject(undefined))
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateProject', () => {
  // [HAPPY] POSTs to /me/projects
  it('POSTs to /me/projects', async () => {
    let capturedBody: Record<string, unknown> | null = null
    server.use(
      http.post(`${BASE}/me/projects`, async ({ request }) => {
        capturedBody = await request.json() as Record<string, unknown>
        return HttpResponse.json(
          { id: 'proj_new', name: 'New Site', status: 'active' },
          { status: 201 },
        )
      }),
    )

    const { result } = renderHookWithClient(() => useCreateProject())

    await result.current.mutateAsync({
      name: 'New Site',
      address: '123 Main St',
    })

    expect(capturedBody).not.toBeNull()
    expect(capturedBody!.name).toBe('New Site')
    expect(capturedBody!.address).toBe('123 Main St')
  })

  // [ERROR] 404 propagated
  it('propagates error responses', async () => {
    server.use(
      http.post(`${BASE}/me/projects`, () =>
        HttpResponse.json({ detail: 'Validation error' }, { status: 400 }),
      ),
    )

    const { result } = renderHookWithClient(() => useCreateProject())

    await expect(
      result.current.mutateAsync({
        name: '',
        address: '',
      }),
    ).rejects.toThrow()
  })
})
