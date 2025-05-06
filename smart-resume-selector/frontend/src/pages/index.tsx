import { useState, useEffect } from 'react';
import Head from 'next/head';
import axios from 'axios';
import { toast } from 'react-toastify';
import ResumeUploader from '../components/ResumeUploader';
import SearchBar from '../components/SearchBar';
import ResumeList from '../components/ResumeList';
import FilterPanel from '../components/FilterPanel';

export default function Home() {
  const [resumes, setResumes] = useState([]);
  const [filteredResumes, setFilteredResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    skills: [],
    category: '',
    experience_years_min: '',
    experience_years_max: ''
  });
  const [allSkills, setAllSkills] = useState([]);

  // Fetch all resumes on component mount
  useEffect(() => {
    fetchResumes();
    fetchSkills();
  }, []);

  // Fetch all resumes
  const fetchResumes = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/resumes');
      setResumes(response.data);
      setFilteredResumes(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching resumes:', error);
      toast.error('Failed to fetch resumes');
      setIsLoading(false);
    }
  };

  // Fetch all skills for filtering
  const fetchSkills = async () => {
    try {
      const response = await axios.get('/api/skills');
      setAllSkills(response.data.skills);
    } catch (error) {
      console.error('Error fetching skills:', error);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.info('Please enter a search query');
      return;
    }

    try {
      setIsLoading(true);
      const response = await axios.post('/api/resumes/search', {
        query: searchQuery,
        filters: Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v && (Array.isArray(v) ? v.length > 0 : true))
        )
      });
      
      setFilteredResumes(response.data);
      setIsLoading(false);
      
      if (response.data.length === 0) {
        toast.info('No matching resumes found');
      } else {
        toast.success(`Found ${response.data.length} matching resumes`);
      }
    } catch (error) {
      console.error('Error searching resumes:', error);
      toast.error('Failed to search resumes');
      setIsLoading(false);
    }
  };

  // Handle resume upload completion
  const handleUploadComplete = () => {
    fetchResumes();
    toast.success('Resume uploaded successfully');
  };

  // Handle filter changes
  const handleFilterChange = (newFilters) => {
    setFilters({ ...filters, ...newFilters });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Smart Resume Selector</title>
        <meta name="description" content="Smart Resume Selector using regex extraction, Mistral LLM, and semantic search" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center text-primary-700 mb-8">
          Smart Resume Selector
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="md:col-span-1">
            <div className="card mb-6">
              <h2 className="text-xl font-semibold mb-4">Upload Resumes</h2>
              <ResumeUploader onUploadComplete={handleUploadComplete} />
            </div>
            
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Filters</h2>
              <FilterPanel 
                filters={filters} 
                onFilterChange={handleFilterChange} 
                allSkills={allSkills} 
              />
            </div>
          </div>
          
          <div className="md:col-span-3">
            <div className="card mb-6">
              <h2 className="text-xl font-semibold mb-4">Search Resumes</h2>
              <SearchBar 
                searchQuery={searchQuery} 
                setSearchQuery={setSearchQuery} 
                handleSearch={handleSearch} 
                isLoading={isLoading} 
              />
            </div>
            
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Results</h2>
              <ResumeList 
                resumes={filteredResumes} 
                isLoading={isLoading} 
              />
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-gray-100 py-6">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p>Smart Resume Selector &copy; 2025 - Using regex extraction, Mistral LLM, and semantic search</p>
        </div>
      </footer>
    </div>
  );
}
