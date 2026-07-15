import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '大学生成长赋能平台',
  description: '发现自我，规划未来。通过专业测评生成你的成长画像。',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
