import React, { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { Paper, chatWithPapers, PaperItem, getGeminiModels, getOpenAIModels, GeminiModel } from '@/lib/api';
import { X, Send, Bot, Settings, ChevronDown, ChevronUp, Maximize2, Minimize2, Edit3 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface ChatPanelProps {
    selectedPapers: Paper[];
    onClose: () => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    isError?: boolean;
}

export default function ChatPanel({ selectedPapers, onClose }: ChatPanelProps) {
    const { data: session } = useSession();
    const userEmail = session?.user?.email || 'default';
    
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [model, setModel] = useState<'openai' | 'gemini'>('gemini');
    const [showApiKeyManager, setShowApiKeyManager] = useState(false);

    const [apiKeys, setApiKeys] = useState({ openai: '', gemini: '' });
    const [geminiModels, setGeminiModels] = useState<GeminiModel[]>([]);
    const [selectedGeminiModel, setSelectedGeminiModel] = useState<string>('');
    const [openaiModels, setOpenaiModels] = useState<GeminiModel[]>([]);
    const [selectedOpenaiModel, setSelectedOpenaiModel] = useState<string>('');
    const [loadingModels, setLoadingModels] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [inputHeight, setInputHeight] = useState(80);
    const [isResizing, setIsResizing] = useState(false);
    const resizeStartRef = useRef<{ startY: number; startHeight: number } | null>(null);
    const [systemPrompt, setSystemPrompt] = useState<string>('You are a rigorous research assistant analyzing academic papers. Follow these guidelines strictly:\n\n1. NEVER make assumptions or inferences beyond what is explicitly stated in the papers. If information is not present, say "This is not addressed in the provided papers."\n\n2. ALWAYS cite your sources. For every claim, reference the specific paper and section/page where the information appears (e.g., "[Paper Title, Section 3.2]" or "[Smith et al., page 5]").\n\n3. Be concise and direct. Avoid unnecessary preambles or conclusions. It\'s acceptable to say "The paper does not provide clear evidence for X" rather than speculating.\n\n4. Quote exact numbers, metrics, and results when available. Precision matters.\n\n5. Pay special attention to:\n   - Hardware requirements and specifications\n   - Performance bottlenecks (memory, compute, bandwidth)\n   - Inference-time constraints and optimizations\n   - GPU utilization and efficiency issues\n   - Trade-offs between model size, speed, and accuracy\n\n6. When discussing hardware or infrastructure pain points, be specific about:\n   - What hardware was used\n   - What limitations were encountered\n   - What improvements or alternatives were suggested\n\nRemember: "It\'s not clear from the papers" is a valid and preferred answer over speculation.');
    const [showPromptEditor, setShowPromptEditor] = useState(false);

    // Helper functions to get/set localStorage with user scope
    const getUserKey = (key: string) => `${userEmail}_${key}`;
    const getItem = (key: string) => localStorage.getItem(getUserKey(key));
    const setItem = (key: string, value: string) => localStorage.setItem(getUserKey(key), value);

    // Load keys from localStorage on mount
    useEffect(() => {
        if (!userEmail) return;
        
        const storedOpenAI = getItem('openai_key');
        const storedGemini = getItem('gemini_key');
        const storedGeminiModel = getItem('gemini_model');
        const storedOpenAIModel = getItem('openai_model');
        console.log('Loading API keys from localStorage:', { openai: storedOpenAI ? 'Found' : 'Not found', gemini: storedGemini ? 'Found' : 'Not found' });
        if (storedOpenAI) {
            setApiKeys(prev => ({ ...prev, openai: storedOpenAI }));
            fetchOpenAIModels(storedOpenAI);
        }
        if (storedGemini) {
            setApiKeys(prev => ({ ...prev, gemini: storedGemini }));
            fetchGeminiModels(storedGemini);
        }
        if (storedGeminiModel) setSelectedGeminiModel(storedGeminiModel);
        if (storedOpenAIModel) setSelectedOpenaiModel(storedOpenAIModel);
        const storedPrompt = getItem('system_prompt');
        if (storedPrompt) setSystemPrompt(storedPrompt);
    }, [userEmail]);

    const saveApiKey = (provider: 'openai' | 'gemini', key: string) => {
        console.log(`Saving ${provider} API key, length: ${key.length}`);
        setApiKeys(prev => ({ ...prev, [provider]: key }));
        setItem(`${provider}_key`, key);
        
        // Fetch available models when key is saved
        if (provider === 'gemini' && key) {
            fetchGeminiModels(key);
        } else if (provider === 'openai' && key) {
            fetchOpenAIModels(key);
        }
    };
    
    const fetchGeminiModels = async (apiKey: string) => {
        setLoadingModels(true);
        try {
            const result = await getGeminiModels(apiKey);
            if (result.models && result.models.length > 0) {
                setGeminiModels(result.models);
                const savedModel = getItem('gemini_model');
                setSelectedGeminiModel(savedModel || result.models[0].name);
            } else if (result.error) {
                console.error('Error fetching Gemini models:', result.error);
            }
        } catch (error) {
            console.error('Failed to fetch Gemini models:', error);
        } finally {
            setLoadingModels(false);
        }
    };
    
    const fetchOpenAIModels = async (apiKey: string) => {
        setLoadingModels(true);
        try {
            const result = await getOpenAIModels(apiKey);
            if (result.models && result.models.length > 0) {
                setOpenaiModels(result.models);
                const savedModel = getItem('openai_model');
                setSelectedOpenaiModel(savedModel || result.models[0].name);
            } else if (result.error) {
                console.error('Error fetching OpenAI models:', result.error);
            }
        } catch (error) {
            console.error('Failed to fetch OpenAI models:', error);
        } finally {
            setLoadingModels(false);
        }
    };

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleResizeStart = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
        resizeStartRef.current = {
            startY: e.clientY,
            startHeight: inputHeight
        };
    };

    useEffect(() => {
        const handleResizeMove = (e: MouseEvent) => {
            if (!isResizing || !resizeStartRef.current) return;
            const deltaY = resizeStartRef.current.startY - e.clientY;
            const newHeight = Math.min(300, Math.max(80, resizeStartRef.current.startHeight + deltaY));
            setInputHeight(newHeight);
        };

        const handleResizeEnd = () => {
            setIsResizing(false);
            resizeStartRef.current = null;
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleResizeMove);
            document.addEventListener('mouseup', handleResizeEnd);
            return () => {
                document.removeEventListener('mousemove', handleResizeMove);
                document.removeEventListener('mouseup', handleResizeEnd);
            };
        }
    }, [isResizing, inputHeight]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);

        try {
            const paperItems: PaperItem[] = selectedPapers.map(p => ({
                url: p.openreview_url || p.paper_url,
                title: p.title
            }));

            const currentKey = model === 'openai' ? apiKeys.openai : apiKeys.gemini;
            console.log('Sending API key:', currentKey ? 'Key present (length: ' + currentKey.length + ')' : 'No key');
            const res = await chatWithPapers(
                paperItems, 
                userMsg, 
                model, 
                currentKey || undefined,
                model === 'gemini' ? selectedGeminiModel : undefined,
                model === 'openai' ? selectedOpenaiModel : undefined,
                systemPrompt
            );
            setMessages(prev => [...prev, { role: 'assistant', content: res.answer }]);
        } catch (error: any) {
            console.error("Chat error:", error);
            const errorMessage = error.message || "Error: Could not fetch answer. Please check your API key.";
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: errorMessage,
                isError: true
            }]);
            setShowApiKeyManager(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`fixed bg-white shadow-2xl border-t border-l border-gray-200 flex flex-col z-50 transition-all duration-300 ${
            isFullscreen 
                ? 'inset-0 rounded-none' 
                : 'bottom-0 right-0 w-full md:w-[600px] h-[600px] rounded-tl-xl animate-in slide-in-from-bottom-10'
        }`}>
            {/* Header */}
            <div className={`flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50 ${isFullscreen ? '' : 'rounded-tl-xl'}`}>
                <div className="flex items-center gap-2">
                    <Bot className="text-blue-600" size={24} />
                    <div>
                        <h3 className="font-semibold text-gray-900">Deep Dive Chat</h3>
                        <p className="text-xs text-gray-500">
                            {selectedPapers.length} paper{selectedPapers.length !== 1 ? 's' : ''} selected
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex bg-gray-200 rounded-lg p-1 mr-2">
                        <button
                            onClick={() => setModel('openai')}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${model === 'openai' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
                        >
                            OpenAI
                        </button>
                        <button
                            onClick={() => setModel('gemini')}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${model === 'gemini' ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
                        >
                            Gemini
                        </button>
                    </div>
                    <button
                        onClick={() => setShowApiKeyManager(true)}
                        className="p-2 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-900 transition-colors"
                        title="Manage API Keys"
                    >
                        <Settings size={18} />
                    </button>
                    <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="p-2 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-900 transition-colors"
                        title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                    >
                        {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </button>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* API Key Manager Modal */}
            {showApiKeyManager && (
                <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-50 flex items-start justify-center p-6 pt-12 animate-in fade-in duration-200 rounded-tl-xl overflow-y-auto">
                    <div className="bg-white shadow-xl border border-gray-200 rounded-xl p-6 w-full max-w-sm max-h-[calc(100vh-120px)] overflow-y-auto">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-gray-900">Model Settings</h3>
                            <button onClick={() => setShowApiKeyManager(false)} className="text-gray-400 hover:text-gray-600">
                                <X size={20} />
                            </button>
                        </div>
                        <p className="text-xs text-gray-500 mb-4">
                            Keys are stored locally in your browser and used only for requests.
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-gray-900 mb-1">OpenAI API Key</label>
                                <input
                                    type="password"
                                    value={apiKeys.openai}
                                    onChange={(e) => saveApiKey('openai', e.target.value)}
                                    placeholder="sk-..."
                                    className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                            </div>
                            {openaiModels.length > 0 && (
                                <div>
                                    <label className="block text-xs font-medium text-gray-900 mb-1">OpenAI Model</label>
                                    <select
                                        value={selectedOpenaiModel}
                                        onChange={(e) => {
                                            setSelectedOpenaiModel(e.target.value);
                                            setItem('openai_model', e.target.value);
                                        }}
                                        className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    >
                                        {openaiModels.map((model) => (
                                            <option key={model.name} value={model.name}>
                                                {model.display_name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}
                            <div>
                                <label className="block text-xs font-medium text-gray-900 mb-1">Gemini API Key</label>
                                <input
                                    type="password"
                                    value={apiKeys.gemini}
                                    onChange={(e) => saveApiKey('gemini', e.target.value)}
                                    placeholder="AIza..."
                                    className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                />
                            </div>
                            {geminiModels.length > 0 && (
                                <div>
                                    <label className="block text-xs font-medium text-gray-900 mb-1">Gemini Model</label>
                                    <select
                                        value={selectedGeminiModel}
                                        onChange={(e) => {
                                            setSelectedGeminiModel(e.target.value);
                                            setItem('gemini_model', e.target.value);
                                        }}
                                        className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                    >
                                        {geminiModels.map((model) => (
                                            <option key={model.name} value={model.name}>
                                                {model.display_name}
                                            </option>
                                        ))}
                                    </select>
                                    <p className="text-xs text-gray-700 mt-1">
                                        {geminiModels.find(m => m.name === selectedGeminiModel)?.description || ''}
                                    </p>
                                </div>
                            )}
                            {loadingModels && (
                                <div className="text-xs text-gray-700">Loading available models...</div>
                            )}
                            
                            {/* System Prompt Editor */}
                            <div className="pt-4 border-t border-gray-200">
                                <div className="flex items-center justify-between mb-2">
                                    <label className="block text-xs font-medium text-gray-900">System Prompt</label>
                                    <button
                                        onClick={() => setShowPromptEditor(!showPromptEditor)}
                                        className="p-1 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
                                        title={showPromptEditor ? "Hide editor" : "Edit prompt"}
                                    >
                                        <Edit3 size={16} />
                                    </button>
                                </div>
                                {showPromptEditor && (
                                    <div>
                                        <textarea
                                            value={systemPrompt}
                                            onChange={(e) => {
                                                setSystemPrompt(e.target.value);
                                                setItem('system_prompt', e.target.value);
                                            }}
                                            className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-500 resize-y min-h-[100px]"
                                            placeholder="Enter system prompt..."
                                        />
                                        <p className="text-xs text-gray-600 mt-1">
                                            This prompt guides how the AI responds to your questions.
                                        </p>
                                    </div>
                                )}
                                {!showPromptEditor && (
                                    <p className="text-xs text-gray-600 line-clamp-2">
                                        {systemPrompt}
                                    </p>
                                )}
                            </div>
                        </div>

                        <button
                            onClick={() => setShowApiKeyManager(false)}
                            className="w-full mt-6 bg-gray-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-800"
                        >
                            Done
                        </button>
                    </div>
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
                {messages.length === 0 && (
                    <div className="text-center py-10 px-6">
                        <p className="text-gray-500 text-sm mb-2">
                            Ask questions about the selected papers.
                        </p>
                        <div className="flex flex-wrap justify-center gap-2">
                            {selectedPapers.slice(0, 3).map(p => (
                                <span key={p.id} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full max-w-[150px] truncate">
                                    {p.title}
                                </span>
                            ))}
                            {selectedPapers.length > 3 && (
                                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                    +{selectedPapers.length - 3} more
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${m.role === 'user'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-gray-100 text-gray-900 rounded-bl-none border border-gray-200'
                            } ${m.isError ? 'bg-red-50 border-red-200 text-red-800' : ''}`}>
                            {m.role === 'assistant' && !m.isError ? (
                                <div className="prose prose-sm max-w-none prose-p:my-2 prose-headings:my-2">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkMath]}
                                        rehypePlugins={[rehypeKatex]}
                                    >
                                        {m.content}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <div className="whitespace-pre-wrap">{m.content}</div>
                            )}
                            {m.isError && (
                                <button
                                    onClick={() => setShowApiKeyManager(true)}
                                    className="mt-2 text-xs font-semibold underline hover:text-red-900"
                                >
                                    Set API Key
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-2xl rounded-bl-none px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-100 bg-white">
                {/* Resize Handle */}
                <div 
                    onMouseDown={handleResizeStart}
                    className="h-2 bg-gray-100 hover:bg-gray-200 cursor-ns-resize flex items-center justify-center transition-colors"
                >
                    <div className="w-12 h-1 bg-gray-400 rounded-full"></div>
                </div>
                
                <div className="p-4 pt-2">
                    <form onSubmit={handleSend} className="flex gap-2 items-end">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend(e as any);
                                }
                            }}
                            placeholder="Ask a question... (Shift+Enter for new line)"
                            style={{ height: `${inputHeight}px`, resize: 'none' }}
                            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex-shrink-0"
                        >
                            <Send size={20} />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
