"use client";

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { searchPapers, Paper, getFilters } from '@/lib/api';
import PaperCard from '@/app/components/PaperCard';
import ChatPanel from '@/app/components/ChatPanel';
import UserMenu from '@/app/components/UserMenu';
import Autocomplete from '@/app/components/Autocomplete';
import BasketDrawer from '@/app/components/BasketDrawer';
import { Search, Filter, ShoppingBasket } from 'lucide-react';

export default function Home() {
    const { data: session, status } = useSession();
    const router = useRouter();

    const [query, setQuery] = useState('');
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState({ affiliation: [] as string[], author: [] as string[], session: [] as string[], day: [] as string[] });
    const [filterOptions, setFilterOptions] = useState<{ affiliations: string[], authors: string[], sessions: string[] }>({ affiliations: [], authors: [], sessions: [] });
    const [limit, setLimit] = useState(10);
    const [threshold, setThreshold] = useState(0.6); // Default similarity threshold (distance 0.4)

    const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);
    const [basket, setBasket] = useState<Paper[]>([]);
    const [showBasket, setShowBasket] = useState(false);
    const [showChat, setShowChat] = useState(false);

    // Load basket from localStorage on mount
    useEffect(() => {
        const savedBasket = localStorage.getItem('deepDiveBasket');
        if (savedBasket) {
            try {
                setBasket(JSON.parse(savedBasket));
            } catch (e) {
                console.error('Failed to load basket:', e);
            }
        }
    }, []);

    // Save basket to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('deepDiveBasket', JSON.stringify(basket));
    }, [basket]);

    useEffect(() => {
        if (status === 'unauthenticated') {
            router.push('/auth/signin');
        }
    }, [status, router]);

    useEffect(() => {
        getFilters().then(setFilterOptions).catch(console.error);
    }, []);

    if (status === 'loading') {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (!session) {
        return null;
    }

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

    const addToBasket = () => {
        const newPapers = selectedPapers.filter(paper => 
            !basket.find(b => b.id === paper.id)
        );
        if (newPapers.length > 0) {
            setBasket([...basket, ...newPapers]);
        }
        setSelectedPapers([]);
    };

    const removeFromBasket = (paperId: string) => {
        setBasket(basket.filter(p => p.id !== paperId));
    };

    const clearBasket = () => {
        if (confirm('Are you sure you want to clear the basket?')) {
            setBasket([]);
        }
    };

    const isPaperInBasket = (paperId: string) => {
        return basket.some(p => p.id === paperId);
    };

    return (
        <main className="min-h-screen bg-gray-50 pb-20">
            {/* Hero Section */}
            <div className="bg-[#22367a] border-b border-[#292e4a] md:sticky md:top-0 z-10 shadow-lg">
                <div className="max-w-5xl mx-auto px-3 sm:px-4 py-3 sm:py-6">
                    <div className="flex items-center justify-between mb-3 sm:mb-4">
                        <div className="flex items-center gap-2 sm:gap-6">
                            <img src="/fractile-logo.png" alt="Fractile" className="h-8 sm:h-12 md:h-16 hidden sm:block" />
                            <div>
                                <h1 className="text-lg sm:text-2xl md:text-3xl font-bold text-white mb-1 sm:mb-2">
                                    NeuriScout: navigate Neurips 2025
                                </h1>
                                <p className="text-xs sm:text-sm text-[#9ec1dc] hidden sm:block">
                                    Explore papers, ask questions, and dive deep with AI.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 sm:gap-3">
                            <button
                                onClick={() => setShowBasket(true)}
                                className="relative px-3 sm:px-4 py-2 bg-[#2596be] text-white rounded-lg hover:bg-[#3aa8d1] transition-colors flex items-center gap-2 text-sm font-medium shadow-sm"
                            >
                                <ShoppingBasket size={18} />
                                <span className="hidden sm:inline">Basket</span>
                                {basket.length > 0 && (
                                    <span className="absolute -top-2 -right-2 bg-[#f26954] text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-sm">
                                        {basket.length}
                                    </span>
                                )}
                            </button>
                            <UserMenu />
                        </div>
                    </div>

                    <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#f26954]" size={20} />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Search papers..."
                                className="w-full pl-10 pr-4 py-2 sm:py-3 rounded-lg border border-[#292e4a] bg-[#22367a] text-white placeholder-[#9ec1dc] focus:outline-none focus:ring-2 focus:ring-[#40569b] focus:border-transparent shadow-sm text-sm sm:text-lg"
                            />
                        </div>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setShowFilters(!showFilters)}
                                className={`flex-1 sm:flex-initial px-3 sm:px-4 py-2 sm:py-3 rounded-lg border flex items-center justify-center gap-2 transition-colors text-sm ${showFilters ? 'bg-[#2596be] border-[#2596be] text-white' : 'border-[#2596be] bg-transparent text-[#2596be] hover:bg-[#2596be] hover:text-white'}`}
                            >
                                <Filter size={18} />
                                <span className="hidden sm:inline">Filters</span>
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex-1 sm:flex-initial bg-[#f26954] text-white px-4 sm:px-8 py-2 sm:py-3 rounded-lg font-medium hover:bg-[#ff7a63] shadow-sm disabled:opacity-50 transition-colors text-sm"
                            >
                                {loading ? 'Searching...' : 'Search'}
                            </button>
                        </div>
                    </form>

                    {showFilters && (
                        <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-in fade-in slide-in-from-top-2">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-2">
                                        Affiliation (select multiple - OR logic)
                                    </label>
                                    <div className="flex flex-wrap gap-2 mb-2 min-h-[24px]">
                                        {filters.affiliation.map((aff, idx) => (
                                            <span key={idx} className="bg-[#40569b] text-white px-2 py-1 rounded-md text-xs flex items-center gap-1">
                                                {aff}
                                                <button 
                                                    type="button"
                                                    onClick={() => setFilters(prev => ({ ...prev, affiliation: prev.affiliation.filter((_, i) => i !== idx) }))} 
                                                    className="hover:text-[#f26954] font-bold"
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                    <Autocomplete
                                        label=""
                                        value=""
                                        onChange={() => {}}
                                        onSelect={(value) => {
                                            if (value && !filters.affiliation.includes(value)) {
                                                setFilters(prev => ({ ...prev, affiliation: [...prev.affiliation, value] }));
                                            }
                                        }}
                                        options={filterOptions.affiliations}
                                        placeholder="e.g., MIT, Google"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-2">
                                        Author (select multiple - OR logic)
                                    </label>
                                    <div className="flex flex-wrap gap-2 mb-2 min-h-[24px]">
                                        {filters.author.map((auth, idx) => (
                                            <span key={idx} className="bg-[#40569b] text-white px-2 py-1 rounded-md text-xs flex items-center gap-1">
                                                {auth}
                                                <button 
                                                    type="button"
                                                    onClick={() => setFilters(prev => ({ ...prev, author: prev.author.filter((_, i) => i !== idx) }))} 
                                                    className="hover:text-[#f26954] font-bold"
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                    <Autocomplete
                                        label=""
                                        value=""
                                        onChange={() => {}}
                                        onSelect={(value) => {
                                            if (value && !filters.author.includes(value)) {
                                                setFilters(prev => ({ ...prev, author: [...prev.author, value] }));
                                            }
                                        }}
                                        options={filterOptions.authors}
                                        placeholder="e.g., Bengio"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-2">
                                        Session (select multiple - OR logic)
                                    </label>
                                    <div className="flex flex-wrap gap-2 mb-2 min-h-[24px]">
                                        {filters.session.map((sess, idx) => (
                                            <span key={idx} className="bg-[#40569b] text-white px-2 py-1 rounded-md text-xs flex items-center gap-1">
                                                {sess}
                                                <button 
                                                    type="button"
                                                    onClick={() => setFilters(prev => ({ ...prev, session: prev.session.filter((_, i) => i !== idx) }))} 
                                                    className="hover:text-[#f26954] font-bold"
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                    <Autocomplete
                                        label=""
                                        value=""
                                        onChange={() => {}}
                                        onSelect={(value) => {
                                            if (value && !filters.session.includes(value)) {
                                                setFilters(prev => ({ ...prev, session: [...prev.session, value] }));
                                            }
                                        }}
                                        options={filterOptions.sessions}
                                        placeholder="e.g., Oral"
                                    />
                                </div>
                            </div>
                            <div className="md:col-span-3">
                                <label className="block text-xs font-medium text-gray-700 mb-2">
                                    Conference Day & Time (select multiple - OR logic)
                                </label>
                                <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                                    {[
                                        { value: '2025-12-03 AM', label: 'Wed Dec 3 AM' },
                                        { value: '2025-12-03 PM', label: 'Wed Dec 3 PM' },
                                        { value: '2025-12-04 AM', label: 'Thu Dec 4 AM' },
                                        { value: '2025-12-04 PM', label: 'Thu Dec 4 PM' },
                                        { value: '2025-12-05 AM', label: 'Fri Dec 5 AM' },
                                        { value: '2025-12-05 PM', label: 'Fri Dec 5 PM' },
                                    ].map((item) => {
                                        const isSelected = filters.day.includes(item.value);
                                        return (
                                            <button
                                                key={item.value}
                                                type="button"
                                                onClick={() => {
                                                    if (isSelected) {
                                                        setFilters(prev => ({ ...prev, day: prev.day.filter(d => d !== item.value) }));
                                                    } else {
                                                        setFilters(prev => ({ ...prev, day: [...prev.day, item.value] }));
                                                    }
                                                }}
                                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                                                    isSelected 
                                                        ? 'bg-[#40569b] text-white' 
                                                        : 'bg-white border border-gray-300 text-gray-700 hover:border-[#40569b]'
                                                }`}
                                            >
                                                {item.label}
                                            </button>
                                        );
                                    })}
                                </div>
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
                                    className="text-sm text-[#f26954] hover:text-[#ff7a63] hover:underline font-medium"
                                >
                                    {selectedPapers.length === papers.length ? 'Deselect All' : 'Select All'}
                                </button>
                                {selectedPapers.length > 0 && (
                                    <button
                                        onClick={addToBasket}
                                        className="bg-[#2596be] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#3aa8d1] shadow-sm animate-in fade-in zoom-in duration-200 flex items-center gap-2"
                                    >
                                        <ShoppingBasket size={16} />
                                        Add to Basket ({selectedPapers.length})
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
                                    inBasket={isPaperInBasket(paper.id)}
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

            {showBasket && (
                <BasketDrawer
                    basket={basket}
                    onRemove={removeFromBasket}
                    onClear={clearBasket}
                    onDeepDive={() => {
                        setShowBasket(false);
                        setShowChat(true);
                    }}
                    onClose={() => setShowBasket(false)}
                />
            )}

            {showChat && (
                <ChatPanel
                    selectedPapers={basket}
                    onClose={() => setShowChat(false)}
                />
            )}

            {/* Footer */}
            <footer className="fixed bottom-0 left-0 right-0 bg-[#22367a] border-t border-[#292e4a] py-3 z-0">
                <div className="max-w-5xl mx-auto px-4 text-center">
                    <p className="text-sm text-[#9ec1dc]">
                        Powered by <a href="https://www.fractile.ai" target="_blank" rel="noopener noreferrer" className="font-semibold text-[#f26954] hover:text-[#ff7a63] transition-colors">Fractile</a> - Radically Accelerate Frontier Model Inference
                    </p>
                </div>
            </footer>
        </main>
    );
}
