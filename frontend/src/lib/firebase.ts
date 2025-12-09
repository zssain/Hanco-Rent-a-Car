import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDN-oN9cYL_DqMGBc7g2MQ0v2xMNw7YQOo",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "hanco-ai.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "hanco-ai",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "hanco-ai.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "803353116256",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:803353116256:web:5d44a78a854be71c60bcfa",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-YY05MMHP9Y",
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
