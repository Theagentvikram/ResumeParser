import React, { useState } from 'react';
import { FiFilter, FiX } from 'react-icons/fi';

const FilterPanel = ({ filters, onFilterChange, allSkills }) => {
  const [showSkillsDropdown, setShowSkillsDropdown] = useState(false);
  
  const categories = [
    'Software Engineering',
    'Data Science',
    'Design',
    'Marketing',
    'Sales',
    'Finance',
    'Human Resources',
    'Operations',
    'Product Management',
    'Customer Support',
    'Professional'
  ];

  const handleSkillSelect = (skill) => {
    const updatedSkills = filters.skills.includes(skill)
      ? filters.skills.filter(s => s !== skill)
      : [...filters.skills, skill];
    
    onFilterChange({ skills: updatedSkills });
  };

  const handleCategoryChange = (e) => {
    onFilterChange({ category: e.target.value });
  };

  const handleExperienceChange = (field, value) => {
    onFilterChange({ [field]: value });
  };

  const clearFilters = () => {
    onFilterChange({
      skills: [],
      category: '',
      min_experience: '',
      max_experience: ''
    });
  };

  return (
    <div>
      {/* Skills filter */}
      <div className="form-group">
        <label className="form-label">Skills</label>
        <div className="relative">
          <button
            type="button"
            className="form-input flex justify-between items-center w-full"
            onClick={() => setShowSkillsDropdown(!showSkillsDropdown)}
          >
            <span>
              {filters.skills.length > 0
                ? `${filters.skills.length} selected`
                : 'Select skills'}
            </span>
            <FiFilter size={16} />
          </button>
          
          {showSkillsDropdown && (
            <div className="absolute z-10 mt-1 w-full bg-white rounded-md shadow-lg max-h-60 overflow-auto border border-gray-200">
              <div className="p-2">
                {allSkills.length > 0 ? (
                  allSkills.map((skill, index) => (
                    <div key={index} className="flex items-center p-2 hover:bg-gray-50 rounded">
                      <input
                        type="checkbox"
                        id={`skill-${index}`}
                        checked={filters.skills.includes(skill)}
                        onChange={() => handleSkillSelect(skill)}
                        className="mr-2"
                      />
                      <label htmlFor={`skill-${index}`} className="cursor-pointer w-full text-sm">
                        {skill}
                      </label>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center p-2 text-sm">No skills available</p>
                )}
              </div>
            </div>
          )}
        </div>
        
        {filters.skills.length > 0 && (
          <div className="skill-tags mt-2">
            {filters.skills.map((skill, index) => (
              <span key={index} className="skill-tag">
                {skill}
                <button
                  type="button"
                  className="skill-tag-remove"
                  onClick={() => handleSkillSelect(skill)}
                  aria-label={`Remove ${skill}`}
                >
                  <FiX size={14} />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Category filter */}
      <div className="form-group">
        <label htmlFor="category" className="form-label">Job Category</label>
        <select
          id="category"
          className="form-select"
          value={filters.category}
          onChange={handleCategoryChange}
        >
          <option value="">All Categories</option>
          {categories.map((category, index) => (
            <option key={index} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      {/* Experience range filter */}
      <div className="form-group">
        <label className="form-label">Experience (years)</label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <input
              type="number"
              className="form-input"
              placeholder="Min"
              min="0"
              max="50"
              value={filters.min_experience}
              onChange={(e) => handleExperienceChange('min_experience', e.target.value)}
            />
          </div>
          <div>
            <input
              type="number"
              className="form-input"
              placeholder="Max"
              min="0"
              max="50"
              value={filters.max_experience}
              onChange={(e) => handleExperienceChange('max_experience', e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Clear filters button */}
      <button
        type="button"
        onClick={clearFilters}
        className="btn btn-outline btn-block mt-4"
      >
        Clear Filters
      </button>
    </div>
  );
};

export default FilterPanel;
