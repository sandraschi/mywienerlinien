import React from 'react';
import { Train, Bus, MapPin, Clock } from 'lucide-react';

export default function Dashboard() {
    const departures = [
        { line: 'U1', destination: 'Oberlaa', time: '2 min', type: 'u-bahn', color: 'bg-red-600' },
        { line: 'U4', destination: 'Heiligenstadt', time: '5 min', type: 'u-bahn', color: 'bg-green-600' },
        { line: '13A', destination: 'Althanstraße', time: '3 min', type: 'bus', color: 'bg-blue-600' },
        { line: 'D', destination: 'Nußdorf', time: '7 min', type: 'tram', color: 'bg-red-500' },
    ];

    return (
        <div className="space-y-8 page-enter">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold gradient-text tracking-tight uppercase">Live Departures</h1>
                    <p className="text-slate-500 mt-1">Real-time traffic data for Vienna (Wien-9-Alt).</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {['U-Bahn', 'Tram', 'Bus', 'S-Bahn'].map((mode) => (
                    <div key={mode} className="glass-card p-6 flex items-center justify-between">
                        <span className="font-bold text-sm tracking-widest uppercase">{mode}</span>
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    </div>
                ))}
            </div>

            <div className="glass-card overflow-hidden">
                <div className="px-6 py-4 border-b border-white/[0.06]">
                    <h3 className="font-bold text-sm tracking-widest uppercase">Next Departures</h3>
                </div>
                <div className="divide-y divide-white/[0.04]">
                    {departures.map((dep, i) => (
                        <div key={i} className="px-6 py-4 hover:bg-white/[0.02] transition-colors flex items-center gap-6">
                            <div className={`w-12 h-10 ${dep.color} rounded flex items-center justify-center font-bold text-lg`}>
                                {dep.line}
                            </div>
                            <div className="flex-1">
                                <p className="font-bold text-white uppercase text-sm">{dep.destination}</p>
                                <p className="text-[10px] text-slate-500 mt-0.5 tracking-wider">{dep.type.toUpperCase()}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xl font-bold text-white tracking-tighter">{dep.time}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
