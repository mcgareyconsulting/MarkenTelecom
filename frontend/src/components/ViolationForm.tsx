import React, { useState, useEffect, useRef } from 'react';
import { PlusCircleIcon } from 'lucide-react';
import { ViolationItem } from './ViolationItem';

type Violation = {
  id: number;
  type: string;
  image: File | null;
  notes: string;
};

type AddressSuggestion = {
  address: string;
  account_number: string;
  account_name: string;
};

export function ViolationForm() {
  const [address, setAddress] = useState('');
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [violations, setViolations] = useState<Violation[]>([{
    id: 1,
    type: '',
    image: null,
    notes: ''
  }]);

  // Ref for the suggestions container
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Function to fetch address suggestions
  const fetchAddressSuggestions = async (query: string) => {
    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/address/autocomplete?q=${encodeURIComponent(query)}&limit=5`);

      if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
      }

      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error fetching address suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle address input change with debounce
  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setAddress(value);

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      fetchAddressSuggestions(value);
    }, 300); // 300ms debounce

    setShowSuggestions(true);
  };

  // Handle suggestion selection
  const handleSelectSuggestion = (suggestion: AddressSuggestion) => {
    setAddress(suggestion.address);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleAddViolation = () => {
    const newId = violations.length > 0 ? Math.max(...violations.map(v => v.id)) + 1 : 1;
    setViolations([...violations, {
      id: newId,
      type: '',
      image: null,
      notes: ''
    }]);
  };

  const updateViolation = (id: number, updates: Partial<Violation>) => {
    setViolations(violations.map(violation => violation.id === id ? {
      ...violation,
      ...updates
    } : violation));
  };

  const removeViolation = (id: number) => {
    if (violations.length > 1) {
      setViolations(violations.filter(violation => violation.id !== id));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would send the data to a server
    console.log({
      address,
      violations
    });
    alert('Report submitted successfully!');
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
      <div className="mb-6 relative">
        <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
          Address
        </label>
        <input
          id="address"
          type="text"
          value={address}
          onChange={handleAddressChange}
          onFocus={() => setShowSuggestions(true)}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter address line 1"
          required
        />

        {/* Address suggestions dropdown */}
        {showSuggestions && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
          >
            {isLoading ? (
              <div className="p-2 text-gray-500">Loading...</div>
            ) : suggestions.length > 0 ? (
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li
                    key={index}
                    onClick={() => handleSelectSuggestion(suggestion)}
                    className="p-2 hover:bg-gray-100 cursor-pointer"
                  >
                    <div className="font-medium">{suggestion.address}</div>
                    <div className="text-sm text-gray-500">
                      {suggestion.account_name} ({suggestion.account_number})
                    </div>
                  </li>
                ))}
              </ul>
            ) : address.length >= 2 ? (
              <div className="p-2 text-gray-500">No suggestions found</div>
            ) : null}
          </div>
        )}
      </div>

      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-800 mb-3">Violations</h2>
        {violations.map(violation => (
          <ViolationItem
            key={violation.id}
            violation={violation}
            updateViolation={updateViolation}
            removeViolation={removeViolation}
            showRemoveButton={violations.length > 1}
          />
        ))}
        <button
          type="button"
          onClick={handleAddViolation}
          className="mt-4 flex items-center text-blue-600 hover:text-blue-800"
        >
          <PlusCircleIcon className="w-5 h-5 mr-1" />
          <span>Add another violation</span>
        </button>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Submit Report
        </button>
      </div>
    </form>
  );
}
