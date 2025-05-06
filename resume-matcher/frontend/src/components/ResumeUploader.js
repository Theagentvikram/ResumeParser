import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUpload, FiFile, FiX } from 'react-icons/fi';
import { uploadResume, uploadBulkResumes } from '../utils/api';
import { toast } from 'react-toastify';

const ResumeUploader = ({ onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles) => {
    // Filter for PDF files
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length < acceptedFiles.length) {
      toast.warning('Only PDF files are accepted');
    }
    
    setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (index) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.info('Please select at least one PDF file');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      let response;
      
      // Track upload progress
      const onProgress = (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total || 100)
        );
        setUploadProgress(percentCompleted);
      };

      // Use bulk upload if multiple files, otherwise use single upload
      if (files.length > 1) {
        response = await uploadBulkResumes(files, onProgress);
        toast.success(`Uploaded ${response.resumes.length} resumes successfully`);
      } else {
        response = await uploadResume(files[0], onProgress);
        toast.success('Resume uploaded successfully');
      }

      // Clear files after successful upload
      setFiles([]);
      setUploadProgress(0);
      
      // Notify parent component
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload resume(s)');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
      >
        <input {...getInputProps()} />
        <FiUpload size={24} style={{ margin: '0 auto', marginBottom: '0.5rem', color: '#3b82f6' }} />
        <p>Drag & drop PDF resumes here, or click to select files</p>
        <p className="text-sm text-gray-500 mt-1">Only PDF files are accepted</p>
      </div>

      {files.length > 0 && (
        <div className="file-list">
          {files.map((file, index) => (
            <div key={index} className="file-item">
              <div className="file-name">
                <FiFile className="mr-2" style={{ display: 'inline' }} />
                {file.name}
              </div>
              <button 
                type="button" 
                className="file-remove" 
                onClick={() => removeFile(index)}
                aria-label="Remove file"
              >
                <FiX />
              </button>
            </div>
          ))}
        </div>
      )}

      {uploading && (
        <div className="mt-3">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-center">{uploadProgress}% Uploaded</p>
        </div>
      )}

      <button
        className="btn btn-primary btn-block mt-3"
        onClick={handleUpload}
        disabled={uploading || files.length === 0}
      >
        {uploading ? 'Uploading...' : `Upload ${files.length > 0 ? `(${files.length} files)` : 'Resumes'}`}
      </button>
    </div>
  );
};

export default ResumeUploader;
