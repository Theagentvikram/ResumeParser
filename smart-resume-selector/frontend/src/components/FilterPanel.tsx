import { useState } from 'react';
import { FiFilter } from 'react-icons/fi';

interface FilterPanelProps {
  filters: {
    skills: string[];
    category: string;
    experience_years_min: string;
    experience_years_max: string;
  };
  onFilterChange: (filters: any) => void;
  allSkills: string[];
}

export default function FilterPanel({ filters, onFilterChange, allSkills }: FilterPanelProps) {
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
    'Customer Support'
  ];

  const handleSkillSelect = (skill: string) => {
    if (filters.skills.includes(skill)) {
      onFilterChange({
        skills: filters.skills.filter(s => s !== skill)
      });
    } else {
      onFilterChange({
        skills: [...filters.skills, skill]
      });
    }
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ category: e.target.value });
  };

  const handleExperienceChange = (field: string, value: string) => {
    onFilterChange({ [field]: value });
  };

  const clearFilters = () => {
    onFilterChange({
      skills: [],
      category: '',
      experience_years_min: '',
      experience_years_max: ''
    });
  };

  return (
    <div className="space-y-4">
      {/* Skills filter */}
      <div>
        <label className="label">Skills</label>
        <div className="relative">
          <button
            type="button"
            className="input w-full flex items-center justify-between"
            onClick={() => setShowSkillsDropdown(!showSkillsDropdown)}
          >
            <span className="truncate">
              {filters.skills.length > 0
                ? `${filters.skills.length} selected`
                : 'Select skills'}
            </span>
            <FiFilter className="ml-2" />
          </button>
          
          {showSkillsDropdown && (
            <div className="absolute z-10 mt-1 w-full bg-white rounded-md shadow-lg max-h-60 overflow-auto">
              <div className="p-2">
                {allSkills.length > 0 ? (
                  allSkills.map((skill, index) => (
                    <div key={index} className="flex items-center p-2 hover:bg-gray-100 rounded">
                      <input
                        type="checkbox"
                        id={`skill-${index}`}
                        checked={filters.skills.includes(skill)}
                        onChange={() => handleSkillSelect(skill)}
                        className="mr-2"
                      />
                      <label htmlFor={`skill-${index}`} className="cursor-pointer w-full">
                        {skill}
                      </label>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center p-2">No skills available</p>
                )}
              </div>
            </div>
          )}
        </div>
        
        {filters.skills.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {filters.skills.map((skill, index) => (
              <span
                key={index}
                className="bg-primary-100 text-primary-800 text-xs px-2 py-1 rounded-full flex items-center"
              >
                {skill}
                <button
                  type="button"
                  className="ml-1 text-primary-600 hover:text-primary-800"
                  onClick={() => handleSkillSelect(skill)}
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Category filter */}
      <div>
        <label htmlFor="category" className="label">Job Category</label>
        <select
          id="category"
          className="input w-full"
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
      <div>
        <label className="label">Experience (years)</label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <input
              type="number"
              className="input w-full"
              placeholder="Min"
              min="0"
              max="50"
              value={filters.experience_years_min}
              onChange={(e) => handleExperienceChange('experience_years_min', e.target.value)}
            />
          </div>
          <div>
            <input
              type="number"
              className="input w-full"
              placeholder="Max"
              min="0"
              max="50"
              value={filters.experience_years_max}
              onChange={(e) => handleExperienceChange('experience_years_max', e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Clear filters button */}
      <button
        type="button"
        onClick={clearFilters}
        className="btn-outline w-full mt-4"
      >
        Clear Filters
      </button>
    </div>
  );
}
