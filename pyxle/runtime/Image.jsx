/**
 * Framework-owned Image component for Pyxle.
 *
 * This component prevents layout shift (CLS) and enables lazy loading by default.
 * Requires `width` and `height` to be specified to calculate aspect ratio.
 *
 * Usage:
 *   import { Image } from 'pyxle/client';
 *
 *   export default function Page() {
 *     return (
 *       <Image
 *         src="/hero.png"
 *         width={800}
 *         height={400}
 *         alt="Hero image"
 *         priority={false}
 *       />
 *     );
 *   }
 */

import React from 'react';

export const Image = React.forwardRef(
  (
    {
      src,
      width,
      height,
      alt = '',
      priority = false,
      lazy = true,
      className,
      style,
      onLoad,
      onError,
      ...props
    },
    ref
  ) => {
    // Calculate aspect ratio to prevent layout shift
    const aspectRatio = width && height ? (width / height).toFixed(4) : undefined;

    // Combine user styles with aspect-ratio preservation
    const containerStyle = {
      position: 'relative',
      width: '100%',
      paddingBottom: aspectRatio ? `${(height / width) * 100}%` : undefined,
      ...style,
    };

    const imgStyle = {
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      objectFit: 'cover',
    };

    // Use native lazy loading if available and not prioritized
    const loading = priority ? 'eager' : lazy ? 'lazy' : undefined;

    return (
      <div style={containerStyle} className={className}>
        <img
          ref={ref}
          src={src}
          alt={alt}
          width={width}
          height={height}
          loading={loading}
          style={imgStyle}
          onLoad={onLoad}
          onError={onError}
          {...props}
        />
      </div>
    );
  }
);

Image.displayName = 'PyxleImage';

export default Image;
