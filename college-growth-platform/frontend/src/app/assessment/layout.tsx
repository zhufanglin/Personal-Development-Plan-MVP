'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const URL_SLUGS = ['holland', 'ability', 'values', 'learning-habit', 'readiness'];

export default function AssessmentLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  const lastSegment = segments.length >= 3 ? segments[segments.length - 1] : '';
  const isInTest = segments.length >= 3 && URL_SLUGS.includes(lastSegment);
  const isInResult = pathname.includes('/result/');
  const isInProfile = pathname.includes('/profile');

  if (isInTest || isInResult || isInProfile) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen">
      {/* Apple-style dark glass navigation — centered links */}
      <nav className="apple-glass-dark sticky top-0 z-50">
        <div className="max-w-[980px] mx-auto px-6 h-12 flex items-center justify-center">
          <div className="flex items-center gap-8">
            <Link href="/assessment" className="text-[12px] text-white/80 hover:text-white transition-colors tracking-wide">
              测评中心
            </Link>
            <Link href="/assessment/profile" className="text-[12px] text-white/80 hover:text-white transition-colors tracking-wide">
              成长画像
            </Link>
          </div>
        </div>
      </nav>

      <main>
        {children}
      </main>

      {/* Apple-style footer */}
      <footer className="bg-[#f5f5f7]">
        <div className="max-w-[980px] mx-auto px-6">
          <div className="border-t border-[#d2d2d7]/60 py-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
              <p className="text-[12px] text-[#86868b]">
                Copyright © 2025 大学生成长赋能平台
              </p>
              <p className="text-[12px] text-[#86868b]">
                发现自我，规划未来
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
