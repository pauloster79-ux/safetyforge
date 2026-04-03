import { initializeApp, type FirebaseApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  sendEmailVerification,
  type User,
  type Auth,
  onAuthStateChanged,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'not-configured',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'not-configured',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'not-configured',
};

const isConfigured =
  firebaseConfig.apiKey !== 'not-configured' &&
  firebaseConfig.apiKey !== '' &&
  firebaseConfig.apiKey !== undefined;

let app: FirebaseApp | null = null;
let auth: Auth | null = null;
let googleProvider: GoogleAuthProvider | null = null;

if (isConfigured) {
  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
  } catch (e) {
    console.warn('Firebase initialization failed:', e);
  }
} else {
  console.warn(
    'Firebase is not configured. Set VITE_FIREBASE_API_KEY, VITE_FIREBASE_AUTH_DOMAIN, and VITE_FIREBASE_PROJECT_ID in .env'
  );
}

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
