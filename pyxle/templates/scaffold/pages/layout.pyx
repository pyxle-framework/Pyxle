import React from 'react';

export const slots = {};
export const createSlots = () => slots;

export default function AppLayout({ children }) {
    return <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-50">{children}</div>;
}
