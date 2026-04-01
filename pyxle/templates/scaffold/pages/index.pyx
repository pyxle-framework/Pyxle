from __future__ import annotations

from datetime import datetime, timezone

from pyxle import __version__

HEAD = """
<title>Pyxle • Next-style starter</title>
<meta name="description" content="Kick off a Pyxle project with a minimal, Next.js inspired landing page." />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="/favicon.ico" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/styles/tailwind.css" />
<style>
  body { font-family: 'Inter', sans-serif; }
</style>
<script>
(function() {
        try {
                var key = 'pyxle-theme-preference';
                var stored = localStorage.getItem(key);
                var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (stored === 'dark' || (!stored && prefersDark)) {
                        document.documentElement.classList.add('dark');
                        document.documentElement.dataset.theme = 'dark';
                } else {
                        document.documentElement.classList.remove('dark');
                        document.documentElement.dataset.theme = 'light';
                }
        } catch (error) {}
})();
</script>
"""

@server
async def load_home(request):
        now = datetime.now(tz=timezone.utc)
        iso_timestamp = now.isoformat()
        display_time = now.strftime("%H:%M:%S UTC")
        return {
                "hero": {
                        "eyebrow": "The Full-Stack Framework for Python",
                        "title": "Build modern web apps with Python & React.",
                        "tagline": "Pyxle seamlessly blends Python backends with React frontends. Forget writing separate APIs—just export your loader and write your components.",
                        "cta": {
                                "label": "Start Building",
                                "href": "https://pyxle.dev/docs",
                        },
                },
                "highlights": [
                        {
                                "label": "Routing",
                                "title": "File-system Routing",
                                "summary": "Intuitive directory structure. Just create .pyx files to define your routes, layouts, and dynamic segments.",
                        },
                        {
                                "label": "DX",
                                "title": "Vite Powered",
                                "summary": "Instant server start, lightning fast HMR, and optimized production builds powered by Vite and esbuild.",
                        },
                        {
                                "label": "Data",
                                "title": "Integrated Loaders",
                                "summary": "Fetch data directly in Python and pass it to React with zero boilerplate. Fully typed and secure.",
                        },
                        {
                                "label": "Design",
                                "title": "Tailwind CSS",
                                "summary": "Utility-first styling out of the box. Build beautiful, responsive interfaces without leaving your JSX.",
                        },
                ],
                "commands": [
                        {"label": "Initialize a project", "command": "pyxle init my-app"},
                        {"label": "Start the dev server", "command": "pyxle dev"},
                        {"label": "Check API health", "command": "curl http://localhost:8000/api/pulse"},
                ],
                "resources": [
                        {
                                "title": "Documentation",
                                "description": "Explore the comprehensive guides and API references.",
                                "href": "https://pyxle.dev/docs",
                        },
                        {
                                "title": "GitHub Repository",
                                "description": "Star the project, report issues, or contribute to the source code.",
                                "href": "https://github.com/shivamsn97/pyxle",
                        },
                        {
                                "title": "Deployment",
                                "description": "Learn how to deploy your Pyxle app to production seamlessly.",
                                "href": "https://github.com/shivamsn97/pyxle/blob/main/docs/deployment/deployment.md",
                        },
                ],
                "telemetry": {
                        "version": __version__,
                        "timestamp": iso_timestamp,
                        "display_time": display_time,
                },
        }

import React, { useEffect, useState } from 'react';
import { Link } from 'pyxle/client';

const THEME_KEY = 'pyxle-theme-preference';

const resolvePreferredTheme = () => {
        if (typeof window === 'undefined') {
                return 'dark'; // Default to dark for that devtool feel
        }
        const stored = window.localStorage.getItem(THEME_KEY);
        if (stored === 'dark' || stored === 'light') {
                return stored;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const ThemeToggle = ({ onToggle, theme }) => (
        <button
                type="button"
                onClick={onToggle}
                className="flex h-9 w-9 items-center justify-center rounded-md border border-gray-200 bg-white text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-800 dark:bg-black dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-gray-100"
                aria-label="Toggle theme"
        >
                {theme === 'dark' ? (
                        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                        </svg>
                ) : (
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                        </svg>
                )}
        </button>
);

const StatCard = ({ label, value, hint }) => (
        <div className="flex flex-col justify-center rounded-xl border border-gray-200 bg-white p-5 transition-colors dark:border-gray-800 dark:bg-black">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
                <div className="mt-2 flex items-baseline gap-2">
                        <p className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">{value}</p>
                        {hint && <span className="text-sm text-gray-500 dark:text-gray-400">{hint}</span>}
                </div>
        </div>
);

const Background = () => (
        <div className="pointer-events-none absolute inset-0 -z-10 flex justify-center overflow-hidden">
                <div className="absolute inset-0 bg-[url('/branding/pyxle-grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] dark:opacity-20 opacity-40"></div>
                <div className="absolute top-0 h-[800px] w-[1200px] rounded-full bg-blue-500/10 blur-[100px] dark:bg-blue-600/10"></div>
                <div className="absolute top-[-200px] h-[600px] w-[600px] rounded-full bg-cyan-500/10 blur-[100px] dark:bg-cyan-600/10"></div>
        </div>
);

export const slots = {};
export const createSlots = () => slots;

export default function Page({ data }) {
        const { hero, highlights, commands, resources, telemetry } = data;
        const [theme, setTheme] = useState('dark');

        useEffect(() => {
                if (typeof window === 'undefined') return;
                const media = window.matchMedia('(prefers-color-scheme: dark)');

                const syncTheme = () => setTheme(resolvePreferredTheme());
                syncTheme();

                const handleChange = (event) => {
                        if (!window.localStorage.getItem(THEME_KEY)) {
                                setTheme(event.matches ? 'dark' : 'light');
                        }
                };

                if (typeof media.addEventListener === 'function') {
                        media.addEventListener('change', handleChange);
                        return () => media.removeEventListener('change', handleChange);
                } else {
                        media.addListener(handleChange);
                        return () => media.removeListener(handleChange);
                }
        }, []);

        useEffect(() => {
                if (typeof document === 'undefined') return;
                const root = document.documentElement;
                root.classList.toggle('dark', theme === 'dark');
                root.dataset.theme = theme;
                if (typeof window !== 'undefined') {
                        window.localStorage.setItem(THEME_KEY, theme);
                }
        }, [theme]);

        const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

        return (
                <div className="min-h-screen bg-white text-gray-900 selection:bg-blue-100 selection:text-blue-900 dark:bg-[#0a0a0a] dark:text-gray-50 dark:selection:bg-blue-900/50 dark:selection:text-blue-200">
                        <Background />

                        <div className="mx-auto max-w-7xl px-6 lg:px-8">
                                <nav className="flex items-center justify-between py-6">
                                        <div className="flex items-center gap-2">
                                                <img src="/branding/pyxle-mark.svg" alt="Pyxle" className="h-8 w-8" />
                                                <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">Pyxle</span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                                <a href="https://github.com/shivamsn97/pyxle" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors" target="_blank" rel="noreferrer">GitHub</a>
                                                <a href="https://pyxle.dev/docs" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors" target="_blank" rel="noreferrer">Docs</a>
                                                <ThemeToggle theme={theme} onToggle={toggleTheme} />
                                        </div>
                                </nav>

                                <main className="pt-20 pb-16 sm:pt-32 sm:pb-24 lg:pb-32">
                                        <div className="text-center flex flex-col items-center">
                                                <div className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-600 dark:border-blue-900/50 dark:bg-blue-900/20 dark:text-blue-400 mb-8">
                                                        <span className="flex h-2 w-2 rounded-full bg-blue-600 dark:bg-blue-400 mr-2 animate-pulse"></span>
                                                        {hero.eyebrow}
                                                </div>
                                                <h1 className="mx-auto max-w-4xl text-5xl font-extrabold tracking-tight text-gray-900 dark:text-white sm:text-7xl">
                                                        Build like <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-300">Next.js</span><br className="hidden sm:block" /> without leaving Python.
                                                </h1>
                                                <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-600 dark:text-gray-400">
                                                        {hero.tagline}
                                                </p>
                                                <div className="mt-10 flex items-center justify-center gap-x-6">
                                                        <a href={hero.cta.href} className="rounded-md bg-gray-900 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200 transition-all">
                                                                {hero.cta.label}
                                                        </a>
                                                        <a href="https://github.com/shivamsn97/pyxle" className="text-sm font-semibold leading-6 text-gray-900 dark:text-white hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                                                                View on GitHub <span aria-hidden="true">&#8594;</span>
                                                        </a>
                                                </div>
                                        </div>

                                        <div className="mt-24 sm:mt-32">
                                                <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
                                                        {highlights.map((item) => (
                                                                <div key={item.title} className="group relative rounded-2xl border border-gray-200 bg-white/50 p-6 hover:bg-gray-50/50 dark:border-gray-800 dark:bg-gray-900/20 dark:hover:bg-gray-900/50 transition-colors">
                                                                        <div className="mb-4 inline-flex h-8 items-center rounded-md bg-gray-100 px-3 text-xs font-medium text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                                                                                {item.label}
                                                                        </div>
                                                                        <h3 className="text-base font-semibold text-gray-900 dark:text-white">{item.title}</h3>
                                                                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{item.summary}</p>
                                                                </div>
                                                        ))}
                                                </div>
                                        </div>

                                        <div className="mt-24 grid gap-8 lg:grid-cols-2 sm:mt-32">
                                                <div className="flex flex-col justify-center">
                                                        <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
                                                                Developer Experience First
                                                        </h2>
                                                        <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
                                                                Pyxle is designed to make you productive from day one. Enjoy a highly optimized development environment with tools you already know and love.
                                                        </p>

                                                        <div className="mt-8 grid grid-cols-2 gap-4">
                                                                <StatCard label="Pyxle CLI" value={`v${telemetry.version}`} hint="latest" />
                                                                <StatCard label="Live Pulse" value={telemetry.display_time} />
                                                        </div>
                                                </div>

                                                <div className="rounded-2xl border border-gray-200 bg-gray-50 p-2 dark:border-gray-800 dark:bg-[#111]">
                                                        <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
                                                                <div className="flex gap-1.5">
                                                                        <div className="h-3 w-3 rounded-full bg-red-400/80 dark:bg-red-500/80"></div>
                                                                        <div className="h-3 w-3 rounded-full bg-amber-400/80 dark:bg-amber-500/80"></div>
                                                                        <div className="h-3 w-3 rounded-full bg-green-400/80 dark:bg-green-500/80"></div>
                                                                </div>
                                                                <div className="ml-4 text-xs font-medium text-gray-500">Terminal</div>
                                                        </div>
                                                        <div className="p-4 font-mono text-sm">
                                                                {commands.map((cmd, idx) => (
                                                                        <div key={idx} className="mb-4 last:mb-0">
                                                                                <div className="text-gray-400 dark:text-gray-500"># {cmd.label}</div>
                                                                                <div className="flex items-center mt-1 text-gray-900 dark:text-gray-300">
                                                                                        <span className="mr-2 text-blue-500">$</span>
                                                                                        <span>{cmd.command}</span>
                                                                                </div>
                                                                        </div>
                                                                ))}
                                                        </div>
                                                </div>
                                        </div>

                                        <div className="mt-24 sm:mt-32">
                                                <div className="flex items-center justify-between mb-8">
                                                        <h2 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
                                                                Resources & Documentation
                                                        </h2>
                                                        <a href="https://pyxle.dev/docs" className="text-sm font-semibold text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300">
                                                                View all resources <span aria-hidden="true">&#8594;</span>
                                                        </a>
                                                </div>
                                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                                        {resources.map((res) => (
                                                                <a key={res.href} href={res.href} className="group relative rounded-xl border border-gray-200 bg-white p-6 hover:border-gray-300 dark:border-gray-800 dark:bg-[#111] dark:hover:border-gray-700 transition-colors">
                                                                        <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400 transition-colors">
                                                                                {res.title}
                                                                        </h3>
                                                                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                                                                                {res.description}
                                                                        </p>
                                                                </a>
                                                        ))}
                                                </div>
                                        </div>
                                </main>

                                <footer className="border-t border-gray-200 py-10 dark:border-gray-800">
                                        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                                        &copy; {new Date().getFullYear()} Pyxle. Released under the MIT License.
                                                </p>
                                                <div className="flex gap-6">
                                                        <a href="https://github.com/shivamsn97/pyxle" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">GitHub</a>
                                                        <a href="https://pypi.org/project/pyxle/" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">PyPI</a>
                                                </div>
                                        </div>
                                </footer>
                        </div>
                </div>
        );
}
