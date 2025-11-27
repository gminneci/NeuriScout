"use client";

import { Paper } from '@/lib/api';
import { X, Trash2, ShoppingBasket } from 'lucide-react';

interface BasketDrawerProps {
    basket: Paper[];
    onRemove: (paperId: string) => void;
    onClear: () => void;
    onDeepDive: () => void;
    onClose: () => void;
}

export default function BasketDrawer({ basket, onRemove, onClear, onDeepDive, onClose }: BasketDrawerProps) {
    return (
        <>
            {/* Backdrop */}
            <div 
                className="fixed inset-0 bg-black/50 z-40 animate-in fade-in duration-200"
                onClick={onClose}
            />
            
            {/* Drawer */}
            <div className="fixed right-0 top-0 bottom-0 w-full sm:w-[500px] bg-white shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-300">
                {/* Header */}
                <div className="bg-[#22367a] text-white px-4 sm:px-6 py-4 flex items-center justify-between border-b border-[#292e4a]">
                    <div className="flex items-center gap-3">
                        <ShoppingBasket size={24} />
                        <div>
                            <h2 className="text-lg sm:text-xl font-bold">Deep Dive Basket</h2>
                            <p className="text-xs sm:text-sm text-[#9ec1dc]">{basket.length} paper{basket.length !== 1 ? 's' : ''}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-white hover:text-[#f26954] transition-colors p-1"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6">
                    {basket.length === 0 ? (
                        <div className="text-center py-12">
                            <ShoppingBasket className="mx-auto text-gray-300 mb-4" size={64} />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Your basket is empty</h3>
                            <p className="text-sm text-gray-500">
                                Search for papers and click "Add to Basket" to collect papers for deep diving.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {basket.map((paper, index) => (
                                <div 
                                    key={paper.id}
                                    className="border border-gray-200 rounded-lg p-3 sm:p-4 hover:border-[#2596be] transition-colors bg-white group"
                                >
                                    <div className="flex gap-3">
                                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-[#22367a] text-white flex items-center justify-center text-xs font-medium">
                                            {index + 1}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-medium text-sm text-gray-900 mb-1 line-clamp-2">
                                                {paper.title}
                                            </h3>
                                            {paper.authors && (
                                                <p className="text-xs text-gray-600 line-clamp-1 mb-1">
                                                    {paper.authors}
                                                </p>
                                            )}
                                            {paper.paper_url && (
                                                <a 
                                                    href={paper.paper_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-xs text-[#2596be] hover:text-[#3aa8d1] hover:underline"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    View PDF
                                                </a>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => onRemove(paper.id)}
                                            className="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 p-1"
                                            title="Remove from basket"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                {basket.length > 0 && (
                    <div className="border-t border-gray-200 p-4 sm:p-6 space-y-3 bg-gray-50">
                        <button
                            onClick={onDeepDive}
                            className="w-full bg-[#2596be] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#3aa8d1] shadow-sm transition-colors text-sm sm:text-base"
                        >
                            Start Deep Dive ({basket.length} paper{basket.length !== 1 ? 's' : ''})
                        </button>
                        <button
                            onClick={onClear}
                            className="w-full border border-gray-300 text-gray-700 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors text-sm flex items-center justify-center gap-2"
                        >
                            <Trash2 size={16} />
                            Clear Basket
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}
