"use client";

import Link from 'next/link';
import { Briefcase } from 'lucide-react';

export default function AppHeader() {
  return (
    <header className="bg-card border-b border-border shadow-sm">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2 text-2xl font-headline font-semibold text-primary hover:opacity-80 transition-opacity">
          <Briefcase className="h-8 w-8" />
          <span>Laiers.ai</span>
        </Link>
        <nav>
          <Link href="/create-job" className="text-foreground hover:text-primary transition-colors">
            Create Job
          </Link>
        </nav>
      </div>
    </header>
  );
}
