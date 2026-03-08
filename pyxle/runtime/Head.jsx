/**
 * Framework-owned Head component for Pyxle.
 *
 * This component allows JSX-based head tag declarations inside .pyx files,
 * providing parity with Next.js <Head> while integrating with Pyxle's
 * compiler-driven head metadata system.
 *
 * Usage:
 *   import { Head } from 'pyxle/client';
 *
 *   export default function Page({ data }) {
 *     return (
 *       <>
 *         <Head>
 *           <title>{data.title} • My App</title>
 *           <meta name="description" content={data.description} />
 *           <meta property="og:image" content={data.ogImage} />
 *         </Head>
 *         <h1>{data.title}</h1>
 *       </>
 *     );
 *   }
 *
 * Notes:
 * - During SSR, Head elements are extracted and merged with HEAD variable entries.
 * - Deterministic merge rules apply (layout → page precedence).
 * - Multiple Head blocks are deduplicated by tag type and attributes.
 */

import React from 'react';

export const Head = React.forwardRef(({ children }, ref) => {
  // This component is purely for metadata extraction by the compiler.
  // It does not render in the DOM. During SSR, the Head elements are
  // collected and injected into the document head by the template system.
  return null;
});

Head.displayName = 'PyxleHead';

export default Head;
