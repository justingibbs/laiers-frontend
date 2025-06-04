
"use client";

import { useState, useEffect } from 'react';

interface FormattedDateProps {
  timestamp: number;
  options?: Intl.DateTimeFormatOptions;
  className?: string;
}

export default function FormattedDate({ timestamp, options, className }: FormattedDateProps) {
  const [dateString, setDateString] = useState<string>('');

  useEffect(() => {
    // Ensure timestamp is valid before creating a Date object
    if (timestamp && typeof timestamp === 'number' && !isNaN(timestamp)) {
      try {
        setDateString(new Date(timestamp).toLocaleDateString(undefined, options));
      } catch (error) {
        console.error("Error formatting date:", error);
        setDateString('Invalid date');
      }
    } else if (timestamp) { // Log if timestamp is present but not a valid number
        console.warn("Invalid timestamp for FormattedDate:", timestamp);
        setDateString('Invalid date');
    }
  }, [timestamp, options]);

  // Render placeholder or null if dateString is not yet set or if timestamp was invalid
  if (!dateString && timestamp) {
    return <span className={className || "text-muted-foreground"}>Loading date...</span>;
  }
  // If timestamp was invalid from the start and resulted in empty dateString, or no timestamp
  if (!dateString) {
    return null; 
  }

  return <span className={className}>{dateString}</span>;
}
