/**
 * Head component for managing document head elements
 * Similar to Next.js's next/head
 */
import { useEffect } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

export function Head({ children }) {
  // Server-side: Extract head elements and register them
  if (typeof window === 'undefined') {
    if (typeof globalThis.__PYXLE_HEAD_REGISTRY__ !== 'undefined') {
      try {
        // Render children to static markup for extraction
        const headMarkup = renderToStaticMarkup(<>{children}</>);
        globalThis.__PYXLE_HEAD_REGISTRY__.register(headMarkup);
      } catch (error) {
        // If rendering fails, skip registration
        console.error('Failed to extract head elements:', error);
      }
    }
  }

  // Client-side: Update the document head during navigation
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // Client-side head updates during navigation
    // This will be implemented in a future phase
    // For now, SSR handles the initial head elements
  }, [children]);

  // Return null - head elements are rendered elsewhere
  return null;
}
