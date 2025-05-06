import { useState } from 'react';
import { FiDownload, FiEye, FiUser, FiAward, FiCalendar, FiTag } from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'react-toastify';

interface Resume {
  resume_id: string;
  name: string;
  summary: string;
  key_skills: string[];
  category: string;
  experience_level: string;
  total_experience_years: number;
  similarity_score: number;
}

interface ResumeListProps {
  resumes: Resume[];
  isLoading: boolean;
}

export default function ResumeList({ resumes, isLoading }: ResumeListProps) {
  const [expandedResume, setExpandedResume] = useState<string | null>(null);

  const toggleExpand = (resumeId: string) => {
    if (expandedResume === resumeId) {
      setExpandedResume(null);
    } else {
      setExpandedResume(resumeId);
    }
  };

  const downloadResume = async (resumeId: string) => {
    try {
      const response = await axios.get(`/api/resumes/${resumeId}/download`, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resume-${resumeId}.pdf`);
      
      // Append to html page
      document.body.appendChild(link);
      
      // Start download
      link.click();
      
      // Clean up and remove the link
      link.parentNode?.removeChild(link);
      
      toast.success('Resume downloaded successfully');
    } catch (error) {
      console.error('Error downloading resume:', error);
      toast.error('Failed to download resume');
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (resumes.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <p>No resumes found. Upload resumes or adjust your search criteria.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {resumes.map((resume) => (
        <div key={resume.resume_id} className="border rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
          <div className="p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{resume.name}</h3>
                <div className="flex flex-wrap gap-2 mt-1">
                  <span className="inline-flex items-center text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded-full">
                    <FiTag className="mr-1" />
                    {resume.category}
                  </span>
                  <span className="inline-flex items-center text-xs bg-secondary-100 text-secondary-800 px-2 py-1 rounded-full">
                    <FiUser className="mr-1" />
                    {resume.experience_level}
                  </span>
                  <span className="inline-flex items-center text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full">
                    <FiCalendar className="mr-1" />
                    {resume.total_experience_years} years
                  </span>
                  {resume.similarity_score && (
                    <span className="inline-flex items-center text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      <FiAward className="mr-1" />
                      {Math.round(resume.similarity_score * 100)}% match
                    </span>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => toggleExpand(resume.resume_id)}
                  className="btn-outline py-1 px-2 text-sm"
                >
                  <FiEye className="mr-1 inline" />
                  {expandedResume === resume.resume_id ? 'Hide' : 'View'}
                </button>
                <button
                  onClick={() => downloadResume(resume.resume_id)}
                  className="btn-primary py-1 px-2 text-sm"
                >
                  <FiDownload className="mr-1 inline" />
                  Download
                </button>
              </div>
            </div>
            
            <div className="mt-2">
              <p className="text-gray-600 text-sm line-clamp-2">
                {resume.summary}
              </p>
            </div>
            
            {expandedResume === resume.resume_id && (
              <div className="mt-4 border-t pt-4">
                <h4 className="text-sm font-medium mb-2">Key Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {resume.key_skills.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
                
                <div className="mt-4">
                  <h4 className="text-sm font-medium mb-2">Full Summary</h4>
                  <p className="text-gray-600 text-sm">{resume.summary}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
