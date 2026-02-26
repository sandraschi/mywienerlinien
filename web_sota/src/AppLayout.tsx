import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
    Train,
    Bus,
    Clock,
    MapPin,
    AlertTriangle,
    Menu,
    X,
    Search,
    ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AppLayout() {
    const [isOpen, setIsOpen] = useState(true);

    const navItems = [
        { title: 'Departures', icon: Clock, path: '/dashboard' },
        { title: 'Subway (U-Bahn)', icon: Train, path: '/subway' },
        { title: 'Bus & Tram', icon: Bus, path: '/surface' },
        { title: 'Network Map', icon: MapPin, path: '/map' },
        { title: 'Disturbances', icon: AlertTriangle, path: '/alerts' },
    ];

    return (
        <div className="flex min-h-screen bg-[#050505]">
            <aside className={cn("glass-sidebar transition-all duration-300", isOpen ? "w-64" : "w-20")}>
                <div className="p-6 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#E31C3D] flex items-center justify-center flex-shrink-0">
                        <Train className="w-5 h-5 text-white" />
                    </div>
                    {isOpen && <span className="font-bold text-lg gradient-text">Wiener Linien</span>}
                </div>
                <nav className="flex-1 px-3 space-y-1 mt-4">
                    {navItems.map((item) => (
                        <NavLink key={item.path} to={item.path} className={({ isActive }) => cn("nav-item", isActive && "active", !isOpen && "justify-center")}>
                            <item.icon className="w-5 h-5" />
                            {isOpen && <span>{item.title}</span>}
                        </NavLink>
                    ))}
                </nav>
            </aside>

            <main className={cn("flex-1 px-8 py-16", isOpen ? "ml-64" : "ml-20")}>
                <Outlet />
            </main>
        </div>
    );
}
