'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Paper } from '@/lib/api';

interface BookmarksContextType {
    bookmarks: Paper[];
    addBookmark: (paper: Paper) => void;
    removeBookmark: (paperId: string) => void;
    isBookmarked: (paperId: string) => boolean;
    clearBookmarks: () => void;
}

const BookmarksContext = createContext<BookmarksContextType | undefined>(undefined);

const BOOKMARKS_STORAGE_KEY = 'neuriscout_bookmarks';

export function BookmarksProvider({ children }: { children: ReactNode }) {
    const [bookmarks, setBookmarks] = useState<Paper[]>([]);
    const [isLoaded, setIsLoaded] = useState(false);

    // Load bookmarks from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(BOOKMARKS_STORAGE_KEY);
            if (stored) {
                setBookmarks(JSON.parse(stored));
            }
        } catch (error) {
            console.error('Failed to load bookmarks:', error);
        }
        setIsLoaded(true);
    }, []);

    // Save bookmarks to localStorage whenever they change
    useEffect(() => {
        if (isLoaded) {
            try {
                localStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify(bookmarks));
            } catch (error) {
                console.error('Failed to save bookmarks:', error);
            }
        }
    }, [bookmarks, isLoaded]);

    const addBookmark = (paper: Paper) => {
        setBookmarks((prev) => {
            // Avoid duplicates
            if (prev.some((p) => p.id === paper.id)) {
                return prev;
            }
            return [...prev, paper];
        });
    };

    const removeBookmark = (paperId: string) => {
        setBookmarks((prev) => prev.filter((p) => p.id !== paperId));
    };

    const isBookmarked = (paperId: string) => {
        return bookmarks.some((p) => p.id === paperId);
    };

    const clearBookmarks = () => {
        setBookmarks([]);
        // Immediately clear localStorage to ensure it's saved
        try {
            localStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify([]));
        } catch (error) {
            console.error('Failed to clear bookmarks from localStorage:', error);
        }
    };

    return (
        <BookmarksContext.Provider
            value={{
                bookmarks,
                addBookmark,
                removeBookmark,
                isBookmarked,
                clearBookmarks,
            }}
        >
            {children}
        </BookmarksContext.Provider>
    );
}

export function useBookmarks() {
    const context = useContext(BookmarksContext);
    if (context === undefined) {
        throw new Error('useBookmarks must be used within a BookmarksProvider');
    }
    return context;
}
