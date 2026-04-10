import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useWorkers, useExpiringCertifications, useCertificationMatrix } from './useWorkers'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/workers`, ({ request }) => {
    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const workers = [
      { id: 'wkr_1', first_name: 'John', last_name: 'Doe', status: 'active', role: 'foreman' },
      { id: 'wkr_2', first_name: 'Jane', last_name: 'Smith', status: 'inactive', role: 'laborer' },
    ]
    const filtered = status ? workers.filter(w => w.status === status) : workers
    return HttpResponse.json({ workers: filtered, total: filtered.length })
  }),
  http.get(`${BASE}/me/workers/expiring-certifications`, () =>
    HttpResponse.json({
      certifications: [
        {
          worker_id: 'wkr_1',
          worker_name: 'John Doe',
          certification: { id: 'cert_1', certification_type: 'OSHA-10', expiry_date: '2026-04-15', status: 'expiring_soon' },
        },
        {
          worker_id: 'wkr_2',
          worker_name: 'Jane Smith',
          certification: { id: 'cert_2', certification_type: 'First Aid', expiry_date: '2026-04-20', status: 'expiring_soon' },
        },
      ],
      total: 2,
    }),
  ),
  http.get(`${BASE}/me/workers/certification-matrix`, () =>
    HttpResponse.json({
      matrix: [
        { worker_id: 'wkr_1', worker_name: 'John Doe', role: 'foreman', 'OSHA-10': 'valid', 'First Aid': 'expired' },
        { worker_id: 'wkr_2', worker_name: 'Jane Smith', role: 'laborer', 'OSHA-10': 'valid', 'First Aid': 'valid' },
      ],
      total: 2,
    }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useWorkers', () => {
  // [HAPPY] List workers and unwrap envelope
  it('fetches from /me/workers and unwraps .workers', async () => {
    const { result } = renderHookWithClient(() => useWorkers())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('wkr_1')
  })

  // [HAPPY] Passes status filter as query param
  it('passes status filter as query parameter', async () => {
    const { result } = renderHookWithClient(() => useWorkers({ status: 'active' }))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].status).toBe('active')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no workers exist', async () => {
    server.use(
      http.get(`${BASE}/me/workers`, () =>
        HttpResponse.json({ workers: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useWorkers())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useExpiringCertifications', () => {
  // [HAPPY] Fetches expiring certifications and unwraps .certifications
  it('fetches from /me/workers/expiring-certifications and unwraps .certifications', async () => {
    const { result } = renderHookWithClient(() => useExpiringCertifications())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].worker_id).toBe('wkr_1')
    expect(result.current.data![0].certification.certification_type).toBe('OSHA-10')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no certifications are expiring', async () => {
    server.use(
      http.get(`${BASE}/me/workers/expiring-certifications`, () =>
        HttpResponse.json({ certifications: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useExpiringCertifications())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useCertificationMatrix', () => {
  // [HAPPY] Fetches certification matrix and unwraps .matrix
  it('fetches from /me/workers/certification-matrix and unwraps .matrix', async () => {
    const { result } = renderHookWithClient(() => useCertificationMatrix())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].worker_id).toBe('wkr_1')
    expect(result.current.data![0].role).toBe('foreman')
  })

  // [EDGE] Empty matrix unwraps to empty array
  it('returns empty array when matrix is empty', async () => {
    server.use(
      http.get(`${BASE}/me/workers/certification-matrix`, () =>
        HttpResponse.json({ matrix: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useCertificationMatrix())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})
