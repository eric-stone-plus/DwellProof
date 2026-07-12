import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DwellProof - 二手房投资证据工作台",
  description: "可追溯、可复算、证据不足时拒绝给结论的二手房投资分析工具。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
