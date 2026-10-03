import type { Metadata } from "next";
import { Geist_Mono, Tajawal } from "next/font/google";
import "./globals.css";

/** Tajawal — الخط الأساسي للمنصة (يدعم العربية والإنجليزية معاً). */
const tajawal = Tajawal({
  variable: "--font-tajawal",
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "700", "800", "900"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "منظومة النور — أتمتة دورة العطاءات الهندسية",
  description:
    "منظومة ويب عربية موحدة: رصد المنافسات الحكومية، تحليل كراسات الشروط، توليد العروض الفنية، وتدقيق الامتثال بـ 37 وكيل ذكاء اصطناعي قبل التقديم.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${tajawal.variable} ${geistMono.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
