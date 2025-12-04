import React, { useState } from 'react';
import { Paper } from '@/lib/api';
import { ExternalLink, ChevronDown, ChevronUp, Sparkles, Star } from 'lucide-react';
import { useBookmarks } from '@/contexts/BookmarksContext';

interface PaperCardProps {
    paper: Paper;
    inDeepDive?: boolean;
    deepDiveFull?: boolean;
    onToggleDeepDive: () => void;
}

export default function PaperCard({ paper, inDeepDive, deepDiveFull, onToggleDeepDive }: PaperCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const { isBookmarked, addBookmark, removeBookmark } = useBookmarks();
    const bookmarked = isBookmarked(paper.id);

    const handleToggleBookmark = () => {
        if (bookmarked) {
            removeBookmark(paper.id);
        } else {
            addBookmark(paper);
        }
    };

    return (
        <div
            className={`bg-white rounded-lg sm:rounded-xl shadow-sm border transition-all relative ${
                inDeepDive ? 'border-[#2596be] ring-1 ring-[#2596be]' : 'border-gray-100 hover:shadow-md'
            }`}
        >
            {inDeepDive && (
                <div className="absolute top-2 right-2 bg-[#2596be] text-white px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1 shadow-sm z-10">
                    <Sparkles size={12} />
                    In Deep Dive
                </div>
            )}
            <div className="p-3 sm:p-6 space-y-3">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 sm:gap-4">
                    <div className="flex-1 min-w-0">
                        <h3 className="text-sm sm:text-lg font-semibold text-gray-900 leading-tight">
                            {paper.title}
                        </h3>
                        <p className="text-sm text-gray-500 mt-2 line-clamp-1">
                            {paper.authors}
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-2 shrink-0">
                        <div className="flex flex-wrap justify-end gap-1 max-w-[280px]">
                            {paper.session ? paper.session.split(';').map((s, i) => (
                                <span key={i} className="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-700 rounded-full whitespace-nowrap">
                                    {s.trim()}
                                </span>
                            )) : (
                                <span className="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-700 rounded-full whitespace-nowrap">
                                    Poster
                                </span>
                            )}
                        </div>
                        <div className="flex flex-wrap justify-end gap-1 max-w-[280px]">
                            {paper.affiliation ? paper.affiliation.split(';').map((a, i) => (
                                <span
                                    key={i}
                                    className="text-xs font-medium px-2 py-1 bg-purple-50 text-purple-700 rounded-full whitespace-nowrap max-w-[150px] truncate"
                                    title={a.trim()}
                                >
                                    {a.trim()}
                                </span>
                            )) : (
                                <span className="text-xs font-medium px-2 py-1 bg-purple-50 text-purple-700 rounded-full whitespace-nowrap">
                                    Unknown
                                </span>
                            )}
                        </div>
                        {paper.rating !== undefined && paper.rating > 0 && (
                            <div className="flex items-center gap-1 text-xs font-bold px-2 py-1 bg-amber-50 text-amber-700 rounded-full border border-amber-200">
                                <span>⭐</span>
                                <span>{paper.rating.toFixed(1)}</span>
                            </div>
                        )}
                        {paper.distance !== undefined && (
                            <span
                                className={`text-xs font-bold px-2 py-1 rounded-full ${
                                    (1 - paper.distance) >= 0.8
                                        ? 'bg-green-100 text-green-700'
                                        : (1 - paper.distance) >= 0.6
                                            ? 'bg-yellow-100 text-yellow-700'
                                            : 'bg-gray-100 text-gray-700'
                                }`}
                            >
                                {Math.round((1 - paper.distance) * 100)}% Match
                            </span>
                        )}
                    </div>
                </div>

                <div className={`text-sm text-gray-600 ${isExpanded ? '' : 'line-clamp-3'}`}>
                    {paper.abstract}
                </div>

                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-2"
                >
                    {isExpanded ? <><ChevronUp size={14} /> Show Less</> : <><ChevronDown size={14} /> Show More</>}
                </button>

                <div className="border-t pt-4 mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-3 text-sm text-gray-700 flex-wrap">
                        {paper.neurips_virtualsite_url && (
                            <a
                                href={paper.neurips_virtualsite_url.startsWith('http') 
                                    ? paper.neurips_virtualsite_url 
                                    : `https://neurips.cc${paper.neurips_virtualsite_url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 font-medium hover:text-blue-600 transition-colors"
                            >
                                <ExternalLink size={16} />
                                View on NeurIPS
                            </a>
                        )}
                        {paper.openreview_url && (
                            <a
                                href={paper.openreview_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 font-medium hover:text-blue-600 transition-colors"
                            >
                                <ExternalLink size={16} />
                                Paper
                            </a>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleToggleBookmark}
                            className={`flex items-center justify-center gap-2 text-sm font-medium px-3 py-2 rounded-lg transition-colors shadow-sm ${
                                bookmarked
                                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                            title={bookmarked ? 'Remove from bookmarks' : 'Add to bookmarks'}
                        >
                            <Star size={16} fill={bookmarked ? 'currentColor' : 'none'} />
                        </button>
                        <button
                            onClick={() => {
                                if (!inDeepDive && deepDiveFull) {
                                    return;
                                }
                                onToggleDeepDive();
                            }}
                            disabled={!inDeepDive && !!deepDiveFull}
                            className={`flex items-center justify-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-colors shadow-sm ${
                                inDeepDive
                                    ? 'bg-[#22367a] text-white hover:bg-[#31488e]'
                                    : deepDiveFull
                                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                        : 'bg-[#2596be] text-white hover:bg-[#3aa8d1]'
                            }`}
                            title={(!inDeepDive && deepDiveFull) ? 'Deep Dive is limited to 10 papers' : undefined}
                        >
                            <Sparkles size={16} />
                            {inDeepDive ? 'Remove from Deep Dive' : 'Add to Deep Dive'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
