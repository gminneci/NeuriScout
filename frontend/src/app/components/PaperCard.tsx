import React, { useState } from 'react';
import { Paper } from '@/lib/api';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface PaperCardProps {
    paper: Paper;
    selected: boolean;
    onToggleSelect: () => void;
}

export default function PaperCard({ paper, selected, onToggleSelect }: PaperCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div className={`bg-white rounded-lg sm:rounded-xl shadow-sm border transition-all ${selected ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-100 hover:shadow-md'}`}>
            <div className="p-3 sm:p-6">
                <div className="flex justify-between items-start gap-2 sm:gap-4">
                    <div className="pt-1">
                        <input
                            type="checkbox"
                            checked={selected}
                            onChange={onToggleSelect}
                            className="w-4 h-4 sm:w-5 sm:h-5 rounded border-gray-300 text-[#40569b] focus:ring-[#40569b] cursor-pointer"
                        />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2">
                            <h3 className="text-sm sm:text-lg font-semibold text-gray-900 leading-tight cursor-pointer" onClick={onToggleSelect}>
                                {paper.title}
                            </h3>
                            {paper.distance !== undefined && (
                                <div className="shrink-0 flex flex-col items-start sm:items-end">
                                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${(1 - paper.distance) >= 0.8 ? 'bg-green-100 text-green-700' :
                                        (1 - paper.distance) >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-gray-100 text-gray-700'
                                        }`}>
                                        {Math.round((1 - paper.distance) * 100)}% Match
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 shrink-0">
                        <div className="flex flex-wrap justify-end gap-1 max-w-[300px]">
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
                        <div className="flex flex-wrap justify-end gap-1 max-w-[300px]">
                            {paper.affiliation ? paper.affiliation.split(';').map((a, i) => (
                                <span key={i} className="text-xs font-medium px-2 py-1 bg-purple-50 text-purple-700 rounded-full whitespace-nowrap max-w-[150px] truncate" title={a.trim()}>
                                    {a.trim()}
                                </span>
                            )) : (
                                <span className="text-xs font-medium px-2 py-1 bg-purple-50 text-purple-700 rounded-full whitespace-nowrap">
                                    Unknown
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <p className="text-sm text-gray-500 mt-2 line-clamp-1">
                    {paper.authors}
                </p>

                <div className={`mt-4 text-sm text-gray-600 ${isExpanded ? '' : 'line-clamp-3'}`}>
                    {paper.abstract}
                </div>

                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-xs text-blue-600 mt-2 hover:underline flex items-center gap-1"
                >
                    {isExpanded ? <><ChevronUp size={14} /> Show Less</> : <><ChevronDown size={14} /> Show More</>}
                </button>

                <div className="mt-4 flex items-center gap-3 border-t pt-4">
                    {(paper.openreview_url || paper.paper_url) && (
                        <a
                            href={paper.openreview_url || paper.paper_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
                        >
                            <ExternalLink size={16} />
                            View Paper
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
}
