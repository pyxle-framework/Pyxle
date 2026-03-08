/**
 * ClientOnly component for client-side only rendering
 */
import { useState, useEffect } from 'react';

export function ClientOnly({ children, fallback = null }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return fallback;
  }

  return children;
}
