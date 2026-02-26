import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './AppLayout';

export default function App() {
    return (
        <Routes>
            <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<div className="page-enter"><h1>Live Departures</h1><p className="text-slate-500">Connecting to Wiener Linien API...</p></div>} />
                <Route path="*" element={<div className="p-8">Section WIP</div>} />
            </Route>
        </Routes>
    );
}
