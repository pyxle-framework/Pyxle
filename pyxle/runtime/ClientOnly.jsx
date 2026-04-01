/**
 * Framework-owned ClientOnly wrapper for Pyxle.
 *
 * This component marks sections that should not be server-side rendered.
 * On the server, the fallback (or empty div) is rendered. On the client
 * after hydration, the real children replace the fallback.
 *
 * Use cases:
 * - Third-party libraries that require browser APIs (maps, editors)
 * - Analytics dashboards
 * - Components using localStorage or sessionStorage
 *
 * Usage:
 *   import { ClientOnly } from 'pyxle/client';
 *
 *   export default function Page() {
 *     return (
 *       <>
 *         <h1>Welcome</h1>
 *         <ClientOnly fallback={<Skeleton />}>
 *           <InteractiveMap />
 *         </ClientOnly>
 *       </>
 *     );
 *   }
 */

import React from 'react';

const ClientOnly = React.forwardRef(({ children, fallback }, ref) => {
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return fallback ?? <div />;
  }

  return <>{children}</>;
});

ClientOnly.displayName = 'ClientOnly';

export default ClientOnly;
