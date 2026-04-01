/**
 * Framework-owned Script component for Pyxle.
 *
 * This component is not rendered in the DOM. Instead, it's recognized by the
 * compiler and metadata extractor. The actual script injection happens during
 * SSR (in template.py) and hydration (in client-entry.js).
 *
 * The component exists so developers can import and use it naturally:
 *
 *   import { Script } from 'pyxle/client';
 *
 *   export default function Page() {
 *     return (
 *       <>
 *         <Script src="https://example.com/sdk.js" strategy="afterInteractive" />
 *         <h1>Hello, world</h1>
 *       </>
 *     );
 *   }
 */

export function Script({
  src,
  strategy = 'afterInteractive',
  async = false,
  defer = false,
  module = false,
  noModule = false,
  onLoad,
  onError,
  ...props
}) {
  // This component does not render anything. It's purely for metadata extraction.
  // During SSR, the compiler/metadataadapter recognizes <Script /> and injects
  // the actual <script> tag into the head based on the strategy.
  return null;
}

export default Script;
