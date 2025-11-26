"use client";

import { useState, useEffect } from 'react';
import { searchPapers, Paper, getFilters } from '@/lib/api';
import PaperCard from '@/app/components/PaperCard';
import ChatPanel from '@/app/components/ChatPanel';
import { Search, Filter } from 'lucide-react';

export default function Home() {

    const [query, setQuery] = useState('');
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState({ affiliation: '', author: '', session: '' });
    const [filterOptions, setFilterOptions] = useState<{ affiliations: string[], authors: string[], sessions: string[] }>({ affiliations: [], authors: [], sessions: [] });
    const [limit, setLimit] = useState(10);
    const [threshold, setThreshold] = useState(0.6); // Default similarity threshold (distance 0.4)

    const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);
    const [showChat, setShowChat] = useState(false);

    useEffect(() => {
        getFilters().then(setFilterOptions).catch(console.error);
    }, []);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const results = await searchPapers(query, filters, limit, threshold);
            setPapers(results.results || results);
            setSelectedPapers([]); // Reset selection on new search
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const togglePaperSelection = (paper: Paper) => {
        if (selectedPapers.find(p => p.id === paper.id)) {
            setSelectedPapers(selectedPapers.filter(p => p.id !== paper.id));
        } else {
            setSelectedPapers([...selectedPapers, paper]);
        }
    };

    const selectAll = () => {
        if (selectedPapers.length === papers.length) {
            setSelectedPapers([]);
        } else {
            setSelectedPapers([...papers]);
        }
    };

    return (
        <main className="min-h-screen bg-gray-50 pb-20">
            {/* Hero Section */}
            <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 py-6">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        NeuriScout: navigate Neurips 2025
                    </h1>
                    <p className="text-gray-500 mb-6">
                        Explore papers, ask questions, and dive deep with AI.
                    </p>

                    <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Search for topics (e.g., 'Reinforcement Learning', 'LLM Agents')..."
                                className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm text-lg text-gray-900 placeholder-gray-500"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={() => setShowFilters(!showFilters)}
                            className={`px-4 py-3 rounded-lg border border-gray-300 flex items-center gap-2 hover:bg-gray-50 ${showFilters ? 'bg-blue-50 border-blue-200 text-blue-700' : 'text-gray-700'}`}
                        >
                            <Filter size={20} />
                            Filters
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 shadow-sm disabled:opacity-50 transition-colors"
                        >
                            {loading ? 'Searching...' : 'Search'}
                        </button>
                    </form>

                    {showFilters && (
                        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-in fade-in slide-in-from-top-2">
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Affiliation</label>
                                <input
                                    type="text"
                                    list="affiliations-list"
                                    value={filters.affiliation}
                                    onChange={(e) => setFilters({ ...filters, affiliation: e.target.value })}
                                    placeholder="e.g., MIT, Google"
                                    className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-500"
                                />
                                <datalist id="affiliations-list">
                                    {filterOptions.affiliations.map((opt, i) => <option key={i} value={opt} />)}
                                </datalist>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Author</label>
                                <input
                                    type="text"
                                    list="authors-list"
                                    value={filters.author}
                                    onChange={(e) => setFilters({ ...filters, author: e.target.value })}
                                    placeholder="e.g., Bengio"
                                    className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-500"
                                />
                                <datalist id="authors-list">
                                    {filterOptions.authors.map((opt, i) => <option key={i} value={opt} />)}
                                </datalist>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Session</label>
                                <input
                                    type="text"
                                    list="sessions-list"
                                    value={filters.session}
                                    onChange={(e) => setFilters({ ...filters, session: e.target.value })}
                                    placeholder="e.g., Poster Session 1"
                                    className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-500"
                                />
                                <datalist id="sessions-list">
                                    {filterOptions.sessions.map((opt, i) => <option key={i} value={opt} />)}
                                </datalist>
                            </div>
                            <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-gray-200 pt-4 mt-2">
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                        Max Results: {limit}
                                    </label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="50"
                                        step="5"
                                        value={limit}
                                        onChange={(e) => setLimit(parseInt(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>5</span>
                                        <span>50</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                        Min Similarity: {Math.round((1 - threshold) * 100)}%
                                    </label>
                                    <input
                                        type="range"
                                        min="0.0"
                                        max="1.0"
                                        step="0.05"
                                        value={1 - threshold} // Display as similarity (1 - distance)
                                        onChange={(e) => setThreshold(1 - parseFloat(e.target.value))} // Convert back to distance
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>0%</span>
                                        <span>100%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Results Section */}
            <div className="max-w-5xl mx-auto px-4 py-8">
                {papers && papers.length > 0 ? (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                Found {papers.length} Papers
                            </h2>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={selectAll}
                                    className="text-sm text-blue-600 hover:underline"
                                >
                                    {selectedPapers.length === papers.length ? 'Deselect All' : 'Select All'}
                                </button>
                                {selectedPapers.length > 0 && (
                                    <button
                                        onClick={() => setShowChat(true)}
                                        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm animate-in fade-in zoom-in duration-200"
                                    >
                                        Deep Dive ({selectedPapers.length})
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="grid gap-6">
                            {papers.map((paper) => (
                                <PaperCard
                                    key={paper.id}
                                    paper={paper}
                                    selected={!!selectedPapers.find(p => p.id === paper.id)}
                                    onToggleSelect={() => togglePaperSelection(paper)}
                                />
                            ))}
                        </div>
                    </div>
                ) : (
                    !loading && (
                        <div className="text-center py-20">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                                <Search className="text-gray-400" size={32} />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900">No papers found</h3>
                            <p className="text-gray-500 mt-1">Try adjusting your search or filters.</p>
                        </div>
                    )
                )}
            </div>

            {showChat && (
                <ChatPanel
                    selectedPapers={selectedPapers}
                    onClose={() => setShowChat(false)}
                />
            )}
        </main>
    );
}
