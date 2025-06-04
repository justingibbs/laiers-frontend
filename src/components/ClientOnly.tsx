
"use client";

import { useState, useEffect, type PropsWithChildren } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function ClientOnly({ children }: PropsWithChildren) {
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  if (!hasMounted) {
    // Provide a consistent loading state. Adjust height as needed to prevent layout shifts.
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <LoadingSpinner size={48} />
      </div>
    );
  }

  return <>{children}</>;
}
