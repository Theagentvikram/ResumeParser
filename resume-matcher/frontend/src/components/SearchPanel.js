import React, { useState } from 'react';
import { FiSearch } from 'react-icons/fi';
import { searchResumes } from '../utils/api';
import { toast } from 'react-toastify';

const SearchPanel = ({ onSearchResults, filters }) => {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast.info('Please enter a search query');
      return;
    }
    
    setSearching(true);
    
    try {
      const results = await searchResumes(query, filters);
      
      if (results.length === 0) {
        toast.info('No matching resumes found');
      } else {
        toast.success(`Found ${results.length} matching resumes`);
      }
      
      if (onSearchResults) {
        onSearchResults(results);
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Failed to search resumes');
    } finally {
      setSearching(false);
    }
  };

  return (
    <form onSubmit={handleSearch}>
      <div className="form-group">
        <label htmlFor="search-query" className="form-label">
          Enter recruiter prompt
        </label>
        <div className="flex">
          <div className="relative flex-grow">
            <input
              id="search-query"
              type="text"
              className="form-input pl-10"
              placeholder="e.g., 'Experienced Python developer with AWS skills'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={searching}
            />
            <FiSearch 
              size={18} 
              style={{ 
                position: 'absolute', 
                left: '12px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: '#6b7280'
              }} 
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary ml-2"
            disabled={searching}
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Describe the ideal candidate you're looking for
        </p>
      </div>
      
      <div className="text-sm mt-3 p-3 bg-blue-50 rounded-md border border-blue-100">
        <strong>Pro Tip:</strong> Be specific about skills, experience level, and job requirements for better matches.
      </div>
    </form>
  );
};

export default SearchPanel;
