import React, { useState } from 'react';
import { FiDownload, FiEye, FiEyeOff, FiUser, FiAward, FiCalendar, FiTag } from 'react-icons/fi';
import { downloadResume } from '../utils/api';
import { toast } from 'react-toastify';

const ResumeList = ({ resumes, loading }) => {
  const [expandedResume, setExpandedResume] = useState(null);

  const toggleExpand = (resumeId) => {
    if (expandedResume === resumeId) {
      setExpandedResume(null);
    } else {
      setExpandedResume(resumeId);
    }
  };

  const handleDownload = (resumeId) => {
    try {
      downloadResume(resumeId);
      toast.success('Downloading resume...');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download resume');
    }
  };

  if (loading) {
    return (
      <div className="text-center p-8">
        <div className="spinner"></div>
        <p className="mt-4 text-gray-500">Loading resumes...</p>
      </div>
    );
  }

  if (!resumes || resumes.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <FiUser />
        </div>
        <p className="empty-state-text">No resumes found</p>
        <p className="text-sm text-gray-500">
          Upload some resumes or adjust your search criteria
        </p>
      </div>
    );
  }

  return (
    <div>
      {resumes.map((resume) => (
        <div key={resume.id || resume.resume_id} className="resume-card">
          <div className="resume-card-header">
            <div>
              <h3 className="resume-card-title">{resume.name}</h3>
              <div className="resume-card-meta">
                <span className="badge badge-primary">
                  <FiTag size={12} style={{ marginRight: '4px' }} />
                  {resume.category}
                </span>
                <span className="badge badge-secondary">
                  <FiUser size={12} style={{ marginRight: '4px' }} />
                  {resume.level}
                </span>
                <span className="badge badge-secondary">
                  <FiCalendar size={12} style={{ marginRight: '4px' }} />
                  {resume.experience_years} years
                </span>
                {resume.similarity_score !== undefined && (
                  <span className="badge badge-success">
                    <FiAward size={12} style={{ marginRight: '4px' }} />
                    {Math.round(resume.similarity_score * 100)}% match
                  </span>
                )}
              </div>
            </div>
            <div className="resume-card-actions">
              <button
                className="btn btn-outline btn-sm"
                onClick={() => toggleExpand(resume.id || resume.resume_id)}
              >
                {expandedResume === (resume.id || resume.resume_id) ? (
                  <>
                    <FiEyeOff size={14} style={{ marginRight: '4px' }} />
                    Hide
                  </>
                ) : (
                  <>
                    <FiEye size={14} style={{ marginRight: '4px' }} />
                    View
                  </>
                )}
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => handleDownload(resume.id || resume.resume_id)}
              >
                <FiDownload size={14} style={{ marginRight: '4px' }} />
                Download
              </button>
            </div>
          </div>
          
          <div className="resume-card-summary">
            {resume.summary}
          </div>
          
          {expandedResume === (resume.id || resume.resume_id) && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium mb-2">Skills</h4>
              <div className="skill-tags">
                {resume.skills.map((skill, index) => (
                  <span key={index} className="skill-tag">
                    {skill}
                  </span>
                ))}
              </div>
              
              {resume.email && (
                <div className="mt-3">
                  <h4 className="text-sm font-medium mb-1">Contact</h4>
                  <p className="text-sm">{resume.email}</p>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ResumeList;
