import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { toast } from 'react-toastify';
import { FiUpload, FiFile, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

interface ResumeUploaderProps {
  onUploadComplete: () => void;
}

export default function ResumeUploader({ onUploadComplete }: ResumeUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [files, setFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter for PDF files only
    const pdfFiles = acceptedFiles.filter(
      file => file.type === 'application/pdf'
    );
    
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

  const uploadFiles = async () => {
    if (files.length === 0) {
      toast.info('Please select files to upload');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      
      // Add each file to form data
      files.forEach(file => {
        formData.append('files', file);
      });

      // Upload files
      const response = await axios.post('/api/resumes/upload-bulk', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          setUploadProgress(progress);
        }
      });

      // Clear files after successful upload
      setFiles([]);
      setUploadProgress(100);
      
      // Notify parent component
      onUploadComplete();
      
      toast.success(`Uploaded ${response.data.resumes.length} resumes successfully`);
    } catch (error) {
      console.error('Error uploading files:', error);
      toast.error('Failed to upload files');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />
        <FiUpload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          {isDragActive
            ? 'Drop the PDF files here...'
            : 'Drag & drop PDF files here, or click to select files'}
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Selected Files ({files.length})</h3>
          <ul className="space-y-2 max-h-40 overflow-y-auto">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded">
                <div className="flex items-center">
                  <FiFile className="mr-2 text-gray-500" />
                  <span className="truncate max-w-xs">{file.name}</span>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {uploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary-600 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-1 text-right">{uploadProgress}% Uploaded</p>
        </div>
      )}

      <button
        type="button"
        onClick={uploadFiles}
        disabled={uploading || files.length === 0}
        className="btn-primary w-full flex items-center justify-center"
      >
        {uploading ? (
          <>Processing...</>
        ) : (
          <>
            <FiUpload className="mr-2" />
            Upload {files.length > 0 ? `${files.length} Files` : 'Files'}
          </>
        )}
      </button>
    </div>
  );
}
