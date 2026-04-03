/// <reference types="vitest/globals" />
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
})

// Mock Firebase auth module for tests
vi.mock('@/lib/firebase', () => ({
  isConfigured: true,
  auth: {
    currentUser: {
      getIdToken: vi.fn().mockResolvedValue('test-firebase-token'),
    },
    onAuthStateChanged: vi.fn(),
  },
  googleProvider: {},
  signInWithPopup: vi.fn(),
  signInWithEmailAndPassword: vi.fn(),
  createUserWithEmailAndPassword: vi.fn(),
  signOutUser: vi.fn(),
  sendPasswordResetEmail: vi.fn(),
  sendEmailVerification: vi.fn(),
  onAuthStateChanged: vi.fn(),
}))

// Suppress toast errors in tests
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}))
