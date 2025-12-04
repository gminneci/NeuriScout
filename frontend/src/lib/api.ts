const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Paper {
    id: string;
    title: string;
    abstract: string;
    authors: string;
    affiliation: string;
    session: string;
    paper_url: string;
    neurips_virtualsite_url: string;
    openreview_url: string;
    start_time?: string;
    day?: string;
    ampm?: string;
    poster_position?: string;
    distance: number;
}

export async function searchPapers(
    query: string,
    filters?: { affiliation?: string | string[]; author?: string | string[]; session?: string | string[]; day?: string | string[]; ampm?: string },
    limit?: number,
    threshold?: number
) {
    const body: Record<string, unknown> = { query };
    if (filters) {
        Object.assign(body, filters);
    }
    if (limit !== undefined) body.limit = limit;
    if (threshold !== undefined) body.threshold = threshold;
    const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch papers');
    }
    return response.json();
}

export interface PaperItem {
    url: string;
    title: string;
}

export async function chatWithPapers(
    papers: PaperItem[],
    question: string,
    model: string = "openai",
    api_key?: string,
    gemini_model?: string,
    openai_model?: string,
    system_prompt?: string
) {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ papers, question, model, api_key, gemini_model, openai_model, system_prompt }),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to chat with papers: ${response.status} ${response.statusText} - ${errorText}`);
    }
    return response.json();
}

export async function getFilters() {
    try {
        const response = await fetch(`${API_URL}/filters`);
        if (!response.ok) {
            console.error('Filters fetch failed status', response.status);
            return { affiliations: [], authors: [], sessions: [], days: [], ampm: ['AM','PM'] };
        }
        return response.json();
    } catch (err) {
        console.error('Filters fetch error', err);
        return { affiliations: [], authors: [], sessions: [], days: [], ampm: ['AM','PM'] };
    }
}

export interface GeminiModel {
    name: string;
    display_name: string;
    description: string;
}

export async function getGeminiModels(api_key: string) {
    const response = await fetch(`${API_URL}/gemini-models`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key }),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch Gemini models');
    }
    return response.json();
}

export async function getOpenAIModels(api_key: string) {
    const response = await fetch(`${API_URL}/openai-models`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key }),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch OpenAI models');
    }
    return response.json();
}
