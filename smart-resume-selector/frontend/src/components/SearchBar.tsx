import { FiSearch } from 'react-icons/fi';

interface SearchBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  handleSearch: () => void;
  isLoading: boolean;
}

export default function SearchBar({ 
  searchQuery, 
  setSearchQuery, 
  handleSearch, 
  isLoading 
}: SearchBarProps) {
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="flex items-center">
      <div className="relative flex-grow">
        <input
          type="text"
          className="input w-full pl-10"
          placeholder="Enter recruiter prompt (e.g., 'Experienced Python developer with AWS skills')"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
      </div>
      <button
        className="btn-primary ml-2 whitespace-nowrap"
        onClick={handleSearch}
        disabled={isLoading}
      >
        {isLoading ? 'Searching...' : 'Search'}
      </button>
    </div>
  );
}
