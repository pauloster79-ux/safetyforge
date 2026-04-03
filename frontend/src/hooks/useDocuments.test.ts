import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import {
  useDocuments,
  useRecentDocuments,
  useDocument,
  useDocumentStats,
  useCreateDocument,
} from './useDocuments'

const BASE = 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/documents`, ({ request }) => {
    const url = new URL(request.url)
    const type = url.searchParams.get('type')
    const documents = [
      { id: 'doc_1', title: 'Safety Plan', document_type: 'safety_plan', status: 'draft' },
      { id: 'doc_2', title: 'Risk Assessment', document_type: 'risk_assessment', status: 'completed' },
    ]
    const filtered = type ? documents.filter(d => d.document_type === type) : documents
    return HttpResponse.json({ documents: filtered, total: filtered.length })
  }),
  http.get(`${BASE}/me/documents/stats`, () =>
    HttpResponse.json({
      total_documents: 15,
      documents_this_month: 3,
      by_type: { safety_plan: 5, risk_assessment: 10 },
      by_status: { draft: 4, completed: 11 },
    }),
  ),
  http.get(`${BASE}/me/documents/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, title: 'Safety Plan', document_type: 'safety_plan', status: 'draft' }),
  ),
  http.post(`${BASE}/me/documents`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { id: 'doc_new', title: body.title, document_type: body.document_type, status: 'draft' },
      { status: 201 },
    )
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useDocuments', () => {
  // [HAPPY] List documents and unwrap envelope
  it('fetches documents from /me/documents and unwraps envelope', async () => {
    const { result } = renderHookWithClient(() => useDocuments())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('doc_1')
  })

  // [HAPPY] Passes type filter as query param
  it('passes type filter as query parameter', async () => {
    const { result } = renderHookWithClient(() => useDocuments({ type: 'safety_plan' }))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].document_type).toBe('safety_plan')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no documents match', async () => {
    server.use(
      http.get(`${BASE}/me/documents`, () =>
        HttpResponse.json({ documents: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useDocuments())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useRecentDocuments', () => {
  // [HAPPY] Fetches recent documents and unwraps envelope
  it('fetches recent documents and unwraps .documents', async () => {
    const { result } = renderHookWithClient(() => useRecentDocuments(5))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data!.length).toBeGreaterThan(0)
  })
})

describe('useDocument', () => {
  // [HAPPY] Fetches single document
  it('fetches single document from /me/documents/{id}', async () => {
    const { result } = renderHookWithClient(() => useDocument('doc_1'))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.id).toBe('doc_1')
  })

  // [EDGE] Disabled when id is undefined
  it('does not fetch when id is undefined', () => {
    const { result } = renderHookWithClient(() => useDocument(undefined))
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useDocumentStats', () => {
  // [HAPPY] Returns stats object directly
  it('returns stats object', async () => {
    const { result } = renderHookWithClient(() => useDocumentStats())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.total_documents).toBe(15)
    expect(result.current.data!.documents_this_month).toBe(3)
    expect(result.current.data!.by_type).toBeDefined()
    expect(result.current.data!.by_status).toBeDefined()
  })
})

describe('useCreateDocument', () => {
  // [HAPPY] POSTs to /me/documents
  it('POSTs to /me/documents', async () => {
    let capturedBody: Record<string, unknown> | null = null
    server.use(
      http.post(`${BASE}/me/documents`, async ({ request }) => {
        capturedBody = await request.json() as Record<string, unknown>
        return HttpResponse.json(
          { id: 'doc_new', title: 'New Doc', document_type: 'safety_plan', status: 'draft' },
          { status: 201 },
        )
      }),
    )

    const { result } = renderHookWithClient(() => useCreateDocument())

    await result.current.mutateAsync({
      title: 'New Doc',
      document_type: 'safety_plan',
      project_info: { project_name: 'Test Project' },
    })

    expect(capturedBody).not.toBeNull()
    expect(capturedBody!.title).toBe('New Doc')
    expect(capturedBody!.document_type).toBe('safety_plan')
  })

  // [ERROR] 400 propagated
  it('propagates error responses', async () => {
    server.use(
      http.post(`${BASE}/me/documents`, () =>
        HttpResponse.json({ detail: 'Validation error' }, { status: 400 }),
      ),
    )

    const { result } = renderHookWithClient(() => useCreateDocument())

    await expect(
      result.current.mutateAsync({
        title: '',
        document_type: 'safety_plan',
        project_info: {},
      }),
    ).rejects.toThrow()
  })
})
