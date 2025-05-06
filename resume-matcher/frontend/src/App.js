import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/App.css';

// Import components
import Header from './components/Header';
import ResumeUploader from './components/ResumeUploader';
import SearchPanel from './components/SearchPanel';
import ResumeList from './components/ResumeList';
import FilterPanel from './components/FilterPanel';

// Import API service
import { getAllResumes, getAllSkills } from './utils/api';

function App() {
  const [resumes, setResumes] = useState([]);
  const [filteredResumes, setFilteredResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [skills, setSkills] = useState([]);
  const [filters, setFilters] = useState({
    skills: [],
    category: '',
    min_experience: '',
    max_experience: ''
  });

  // Fetch resumes and skills on component mount
  useEffect(() => {
    fetchResumes();
    fetchSkills();
  }, []);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const data = await getAllResumes();
      setResumes(data);
      setFilteredResumes(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching resumes:', error);
      toast.error('Failed to load resumes');
      setLoading(false);
    }
  };

  const fetchSkills = async () => {
    try {
      const data = await getAllSkills();
      setSkills(data.skills);
    } catch (error) {
      console.error('Error fetching skills:', error);
    }
  };

  const handleUploadSuccess = () => {
    fetchResumes();
    toast.success('Resume uploaded successfully');
  };

  const handleSearchResults = (results) => {
    setFilteredResumes(results);
  };

  const handleFilterChange = (newFilters) => {
    setFilters({ ...filters, ...newFilters });
  };

  return (
    <div className="app">
      <Header />
      <ToastContainer position="top-right" autoClose={3000} />
      
      <main className="main-content">
        <div className="sidebar">
          <section className="section">
            <h2>Upload Resumes</h2>
            <ResumeUploader onUploadSuccess={handleUploadSuccess} />
          </section>
          
          <section className="section">
            <h2>Filters</h2>
            <FilterPanel 
              filters={filters} 
              onFilterChange={handleFilterChange} 
              allSkills={skills} 
            />
          </section>
        </div>
        
        <div className="content">
          <section className="section">
            <h2>Search Resumes</h2>
            <SearchPanel 
              onSearchResults={handleSearchResults} 
              filters={filters} 
            />
          </section>
          
          <section className="section">
            <h2>Results</h2>
            <ResumeList 
              resumes={filteredResumes} 
              loading={loading} 
            />
          </section>
        </div>
      </main>
      
      <footer className="footer">
        <p>Resume Matcher &copy; 2025 - Powered by regex extraction and semantic search</p>
      </footer>
    </div>
  );
}

export default App;
