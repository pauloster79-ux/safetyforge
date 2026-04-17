/**
 * Firebase stub module.
 *
 * Firebase has been replaced by Clerk for authentication.
 * These stubs satisfy any residual imports without pulling in the
 * firebase/app or firebase/auth packages.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

type User = any;
type Auth = any;

const auth: Auth | null = null;
const googleProvider: any | null = null;
const isConfigured = false;

const signInWithPopup: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const signInWithEmailAndPassword: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const createUserWithEmailAndPassword: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const firebaseSignOut: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const sendPasswordResetEmail: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const sendEmailVerification: any = () => Promise.reject(new Error('Firebase is deprecated — use Clerk'));
const onAuthStateChanged: any = () => () => {};

export {
  auth,
  googleProvider,
  isConfigured,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  firebaseSignOut,
  sendPasswordResetEmail,
  sendEmailVerification,
  onAuthStateChanged,
};
export type { User };
