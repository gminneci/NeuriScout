'use client';

import { useState, useRef, useEffect } from 'react';

interface AutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (value: string) => void; // New prop for selection
  options: string[];
  placeholder: string;
  label: string;
}

export default function Autocomplete({ value, onChange, onSelect, options, placeholder, label }: AutocompleteProps) {
  const [inputValue, setInputValue] = useState(value);
  const [isOpen, setIsOpen] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState<string[]>(options);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    // Filter options based on input
    if (inputValue) {
      const filtered = options.filter(opt => 
        opt.toLowerCase().includes(inputValue.toLowerCase())
      );
      setFilteredOptions(filtered);
    } else {
      setFilteredOptions(options);
    }
  }, [inputValue, options]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: string) => {
    if (onSelect) {
      onSelect(option);
      setInputValue(''); // Clear input after selection for multi-select
    } else {
      onChange(option);
      setInputValue(option);
    }
    setIsOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => {
          setInputValue(e.target.value);
          if (!onSelect) {
            onChange(e.target.value);
          }
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-1 focus:ring-[#40569b] text-gray-900 placeholder-gray-500"
      />
      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredOptions.slice(0, 100).map((option, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSelect(option)}
              className="w-full text-left px-3 py-2 text-sm text-gray-900 hover:bg-[#9ec1dc] hover:text-[#22367a] transition-colors border-b border-gray-100 last:border-b-0"
            >
              {option}
            </button>
          ))}
          {filteredOptions.length > 100 && (
            <div className="px-3 py-2 text-xs text-gray-500 text-center">
              Showing first 100 results. Type to filter more.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
