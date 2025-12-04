'use client';

import React from 'react';
import { useBookmarks } from '@/contexts/BookmarksContext';
import { Paper } from '@/lib/api';
import PaperCard from '@/app/components/PaperCard';
import { ArrowLeft, Star, Trash2, Download } from 'lucide-react';
import Link from 'next/link';

export default function BookmarksPage() {
    const { bookmarks, clearBookmarks } = useBookmarks();

    const exportToCSV = () => {
        // CSV header
        const csvRows = ['Day,Time,Poster,Title,Session'];
        
        // Add each bookmark as a row
        bookmarks.forEach(paper => {
            const day = paper.day || '';
            const ampm = paper.ampm || '';
            const poster = paper.poster_position || '';
            const title = (paper.title || '').replace(/"/g, '""'); // Escape quotes
            const session = (paper.session || '').replace(/"/g, '""'); // Escape quotes
            
            csvRows.push(`"${day}","${ampm}","${poster}","${title}","${session}"`);
        });
        
        // Create blob and download
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `neurips-bookmarks-${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    // Group bookmarks by day, then by AM/PM
    const groupedBookmarks = React.useMemo(() => {
        const groups: Record<string, Record<'AM' | 'PM', Paper[]>> = {};

        bookmarks.forEach(paper => {
            const day = paper.day || 'Unknown Date';
            const ampm = (paper.ampm as 'AM' | 'PM') || 'AM';

            if (!groups[day]) {
                groups[day] = { AM: [], PM: [] };
            }
            groups[day][ampm].push(paper);
        });

        // Sort papers within each group by start_time
        Object.keys(groups).forEach(day => {
            groups[day].AM.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
            groups[day].PM.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
        });

        // Sort days chronologically
        const sortedDays = Object.keys(groups).sort();

        return sortedDays.map(day => ({
            day,
            am: groups[day].AM,
            pm: groups[day].PM,
        }));
    }, [bookmarks]);

    const formatDate = (dateStr: string) => {
        if (dateStr === 'Unknown Date') return dateStr;
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch {
            return dateStr;
        }
    };

    const formatTime = (isoTime: string) => {
        if (!isoTime) return '';
        try {
            const date = new Date(isoTime);
            return date.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
        } catch {
            return '';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link 
                            href="/"
                            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            <ArrowLeft size={20} />
                            Back to Search
                        </Link>
                        <div className="h-6 w-px bg-gray-300" />
                        <div className="flex items-center gap-3">
                            <Star size={24} className="text-yellow-600" fill="currentColor" />
                            <h1 className="text-3xl font-bold text-gray-900">
                                My Bookmarks
                            </h1>
                            <span className="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
                                {bookmarks.length}
                            </span>
                        </div>
                    </div>

                    {bookmarks.length > 0 && (
                        <div className="flex gap-2">
                            <button
                                onClick={exportToCSV}
                                className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                            >
                                <Download size={16} />
                                Export CSV
                            </button>
                            <button
                                onClick={() => {
                                    if (confirm(`Are you sure you want to clear all ${bookmarks.length} bookmarks?`)) {
                                        clearBookmarks();
                                    }
                                }}
                                className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                            >
                                <Trash2 size={16} />
                                Clear All
                            </button>
                        </div>
                    )}
                </div>

                {/* Empty state */}
                {bookmarks.length === 0 ? (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
                        <Star size={48} className="text-gray-300 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            No bookmarks yet
                        </h2>
                        <p className="text-gray-600 mb-6">
                            Start bookmarking papers to build your personalized schedule!
                        </p>
                        <Link 
                            href="/"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-[#2596be] text-white rounded-lg hover:bg-[#3aa8d1] transition-colors"
                        >
                            Go to Search
                        </Link>
                    </div>
                ) : (
                    /* Grouped bookmarks */
                    <div className="space-y-8">
                        {groupedBookmarks.map(({ day, am, pm }) => (
                            <div key={day} className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 border-b-2 border-gray-200 pb-2">
                                    {formatDate(day)}
                                </h2>

                                {/* Morning sessions */}
                                {am.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg">
                                                Morning
                                            </span>
                                        </h3>
                                        <div className="space-y-4">
                                            {am.map(paper => (
                                                <div key={paper.id} className="flex gap-3">
                                                    <div className="flex-shrink-0 flex flex-col gap-1 w-20 pt-4">
                                                        {paper.start_time && (
                                                            <div className="text-sm font-medium text-gray-600">
                                                                {formatTime(paper.start_time)}
                                                            </div>
                                                        )}
                                                        {paper.poster_position && (
                                                            <div className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200">
                                                                {paper.poster_position}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex-1">
                                                        <PaperCard 
                                                            paper={paper}
                                                            onToggleDeepDive={() => {}}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Afternoon/Evening sessions */}
                                {pm.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                                            <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-lg">
                                                Afternoon
                                            </span>
                                        </h3>
                                        <div className="space-y-4">
                                            {pm.map(paper => (
                                                <div key={paper.id} className="flex gap-3">
                                                    <div className="flex-shrink-0 flex flex-col gap-1 w-20 pt-4">
                                                        {paper.start_time && (
                                                            <div className="text-sm font-medium text-gray-600">
                                                                {formatTime(paper.start_time)}
                                                            </div>
                                                        )}
                                                        {paper.poster_position && (
                                                            <div className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200">
                                                                {paper.poster_position}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex-1">
                                                        <PaperCard 
                                                            paper={paper}
                                                            onToggleDeepDive={() => {}}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
