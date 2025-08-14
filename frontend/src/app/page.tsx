"use client"

import Link from "next/link"

export default function HomePage() {
  return (
    <main className="relative flex flex-col items-center justify-center min-h-[calc(100vh-56px)] bg-white dark:bg-gradient-to-br dark:from-slate-950 dark:to-slate-900 transition-colors">
      <section className="relative z-10 text-center max-w-2xl mx-auto px-4">
        <h1 className="relative text-5xl md:text-7xl font-black mb-8">
          <span className="relative inline-block">
            <span className="absolute inset-0 bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600 dark:from-white dark:via-amber-100 dark:to-white blur-[2px] bg-clip-text text-transparent animate-gradient opacity-90">
              사주 AI
            </span>
            <span className="relative bg-gradient-to-r from-amber-700 via-orange-600 to-amber-700 dark:from-white dark:via-amber-200 dark:to-white bg-clip-text text-transparent animate-gradient drop-shadow-[0_2px_2px_rgba(0,0,0,0.5)] dark:drop-shadow-[0_2px_2px_rgba(0,0,0,0.3)]">
              사주 AI
            </span>
          </span>
        </h1>
        <p className="text-xl md:text-2xl text-slate-700 dark:text-white mb-12 transition-colors duration-300 font-semibold drop-shadow-sm">
          AI와 함께하는 정확한 사주 분석과 운세 상담
        </p>
        <div className="flex flex-col items-center gap-6 mb-10">
          <Link 
            href="/saju" 
            className="group relative px-16 py-6 rounded-2xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white text-xl font-bold shadow-lg transition-all duration-300 hover:scale-105 dark:from-amber-500 dark:to-orange-500 dark:hover:from-amber-600 dark:hover:to-orange-600"
          >
            <span className="relative z-10">🔮 사주 상담 시작하기</span>
          </Link>
          <div className="text-center text-slate-600 dark:text-slate-400 max-w-lg">
            <p className="text-lg font-medium mb-2">✨ 제공 서비스</p>
            <div className="flex flex-wrap justify-center gap-3 text-sm">
              <span className="px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">사주팔자 분석</span>
              <span className="px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">연간/월간 운세</span>
              <span className="px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">궁합 분석</span>
              <span className="px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">진로 상담</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
