
"use client";

import { useState, useEffect } from 'react';

interface FormattedDateProps {
  timestamp: number;
  options?: Intl.DateTimeFormatOptions;
  className?: string;
}

export default function FormattedDate({ timestamp, options, className }: FormattedDateProps) {
  const [dateToDisplay, setDateToDisplay] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    if (timestamp && typeof timestamp === 'number' && !isNaN(timestamp)) {
      try {
        setDateToDisplay(new Date(timestamp).toLocaleDateString(undefined, options));
      } catch (error) {
        console.error("Error formatting date:", error);
        setDateToDisplay('Invalid date');
      }
    } else if (timestamp) { // Timestamp exists but is not a valid number
      setDateToDisplay('Invalid date');
    } else { // No timestamp provided
      setDateToDisplay(null);
    }
  }, [timestamp, options]);

  if (!isMounted) {
    // Render a consistent, non-layout-shifting placeholder string or nothing.
    // This string is a generic placeholder that aims to reserve similar space.
    // Using a more generic placeholder if no className is provided for styling.
    const placeholder = "--/--/----";
    return <span className={className || "text-muted-foreground text-sm"}>{placeholder}</span>;
  }

  if (dateToDisplay === null) {
    // No timestamp was provided, or it was explicitly cleared.
    return null;
  }

  return <span className={className}>{dateToDisplay}</span>;
}
