import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderHookWithClient } from '@/test/test-utils'
import { useOshaLogEntries, useOsha300Summary } from './useOshaLog'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const server = setupServer(
  http.get(`${BASE}/me/osha-log/entries`, ({ request }) => {
    const url = new URL(request.url)
    const year = url.searchParams.get('year')
    const entries = [
      {
        id: 'osha_1',
        employee_name: 'John Doe',
        date_of_injury: '2026-03-15',
        classification: 'recordable',
        injury_type: 'cut',
      },
      {
        id: 'osha_2',
        employee_name: 'Jane Smith',
        date_of_injury: '2026-02-10',
        classification: 'first_aid',
        injury_type: 'bruise',
      },
    ]
    // Return all entries (year filtering is server-side, we just verify the param is sent)
    if (year) {
      return HttpResponse.json({ entries, total: entries.length })
    }
    return HttpResponse.json({ entries, total: entries.length })
  }),
  http.get(`${BASE}/me/osha-log/summary`, () =>
    HttpResponse.json({
      year: 2026,
      total_cases: 5,
      deaths: 0,
      days_away_from_work_cases: 1,
      job_transfer_cases: 0,
      other_recordable_cases: 4,
      total_days_away: 3,
      total_days_restricted: 0,
      injury_types: { cut: 2, bruise: 3 },
      certified: false,
    }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('useOshaLogEntries', () => {
  // [HAPPY] List entries and unwrap envelope
  it('fetches from /me/osha-log/entries and unwraps .entries', async () => {
    const { result } = renderHookWithClient(() => useOshaLogEntries())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data![0].id).toBe('osha_1')
  })

  // [HAPPY] Passes year filter as query param
  it('passes year as query parameter', async () => {
    let capturedUrl = ''
    server.use(
      http.get(`${BASE}/me/osha-log/entries`, ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({ entries: [], total: 0 })
      }),
    )

    const { result } = renderHookWithClient(() => useOshaLogEntries(2025))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(capturedUrl).toContain('year=2025')
  })

  // [EDGE] Empty list unwraps to empty array
  it('returns empty array when no entries exist', async () => {
    server.use(
      http.get(`${BASE}/me/osha-log/entries`, () =>
        HttpResponse.json({ entries: [], total: 0 }),
      ),
    )
    const { result } = renderHookWithClient(() => useOshaLogEntries())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([])
  })
})

describe('useOsha300Summary', () => {
  // [HAPPY] Returns summary directly (not wrapped in envelope)
  it('returns summary object directly from /me/osha-log/summary', async () => {
    const { result } = renderHookWithClient(() => useOsha300Summary())

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.year).toBe(2026)
    expect(result.current.data!.total_cases).toBe(5)
    expect(result.current.data!.deaths).toBe(0)
    expect(result.current.data!.certified).toBe(false)
  })

  // [HAPPY] Passes year as query param
  it('passes year as query parameter', async () => {
    let capturedUrl = ''
    server.use(
      http.get(`${BASE}/me/osha-log/summary`, ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          year: 2025,
          total_cases: 3,
          deaths: 0,
          days_away_from_work_cases: 0,
          job_transfer_cases: 0,
          other_recordable_cases: 3,
          total_days_away: 0,
          total_days_restricted: 0,
          injury_types: {},
          certified: true,
        })
      }),
    )

    const { result } = renderHookWithClient(() => useOsha300Summary(2025))

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(capturedUrl).toContain('year=2025')
  })

  // [ERROR] Server error propagated
  it('handles server errors', async () => {
    server.use(
      http.get(`${BASE}/me/osha-log/summary`, () =>
        HttpResponse.json({ detail: 'Internal error' }, { status: 500 }),
      ),
    )

    const { result } = renderHookWithClient(() => useOsha300Summary())

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
