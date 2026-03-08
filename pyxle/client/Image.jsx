/**
 * Image component for optimized image loading
 * Similar to Next.js's next/image
 */

export function Image({ 
  src, 
  alt = '',
  width,
  height,
  priority = false,
  lazy = true,
  ...props 
}) {
  // For now, render a standard img tag
  // Future: Add optimization, lazy loading, placeholder, etc.
  return (
    <img 
      src={src} 
      alt={alt} 
      width={width} 
      height={height}
      loading={priority ? 'eager' : lazy ? 'lazy' : 'eager'}
      {...props}
    />
  );
}
