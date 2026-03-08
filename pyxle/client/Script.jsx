/**
 * Script component for optimized script loading
 * Similar to Next.js's next/script
 */

export function Script({ 
  src, 
  strategy = 'afterInteractive',
  async: asyncProp,
  defer,
  onLoad,
  onError,
  children,
  ...props 
}) {
  // During SSR, this component is extracted and handled by the SSR renderer
  // On the client, scripts are loaded according to their strategy
  return null;
}
