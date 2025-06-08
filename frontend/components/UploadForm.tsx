import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';

const UploadForm: React.FC = () => {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [resumeData, setResumeData] = useState<ResumeData | null>(null);

  const handleGenerateSummary = async (file: File) => {
    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a file to analyze.",
        status: "error",
      });
      return;
    }

    // Set loading state
    setIsAnalyzing(true);
    setUploadProgress(10);
    
    // Log what file we're analyzing for debugging
    console.log(`Analyzing resume: ${file.name}`);
    
    try {
      // Simulate realistic progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const increment = Math.floor(Math.random() * 10) + 5;
          const newProgress = Math.min(prev + increment, 90);
          return newProgress;
        });
      }, 800);
      
      // Call backend API
      const result = await analyzeUserResume(file);
      clearInterval(progressInterval);
      
      // Log the complete result for debugging
      console.log('Resume analysis result:', result);
      
      // Ensure a minimum processing time of 3 seconds for better UX
      setTimeout(() => {
        // Always set progress to 100 when done
        setUploadProgress(100);
        
        // Check if there's an error in the result
        if (result.summary && result.summary.toLowerCase().includes('error')) {
          // Error in analysis
          toast({
            title: "Analysis Error",
            description: result.summary,
            status: "error",
            duration: 5000,
          });
          setIsAnalyzing(false);
          return;
        }
        
        // Check if we have skills or if they're error messages
        const validSkills = Array.isArray(result.skills) 
          ? result.skills.filter(skill => 
              typeof skill === 'string' && 
              !skill.toLowerCase().includes('error') &&
              skill.toLowerCase() !== 'error')
          : [];
          
        if (validSkills.length === 0) {
          // No valid skills found - likely an error
          toast({
            title: "Analysis Failed",
            description: "Could not extract skills from your resume. Please check the file format and try again.",
            status: "error",
            duration: 5000,
          });
          setIsAnalyzing(false);
          return;
        }
        
        // Success case - update resume state and navigate
        setResumeData({
          fileName: file.name,
          uploadDate: new Date().toISOString(),
          fileSize: file.size,
          status: "processed",
          summary: result.summary,
          skills: validSkills,
          experience: result.experience,
          educationLevel: result.educationLevel,
          category: result.category,
        });
        
        toast({
          title: "Analysis Complete",
          description: `Successfully analyzed resume with ${validSkills.length} skills identified.`,
          status: "success",
        });
        
        // Navigate to the results page
        router.push("/resume-details");
      }, 1000);
      
    } catch (error) {
      console.error('Resume analysis error:', error);
      setUploadProgress(100);
      
      // Get a useful error message
      let errorMessage = "An unexpected error occurred";
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (typeof error === 'object' && error !== null) {
        errorMessage = String(error);
      }
      
      // Show specific error 
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        status: "error",
        duration: 5000,
      });
    } finally {
      // Ensure loading state is cleared after a delay
      setTimeout(() => {
        setIsAnalyzing(false);
        setUploadProgress(0);
      }, 1500);
    }
  };

  return (
    <div>
      {/* Render your form components here */}
    </div>
  );
};

export default UploadForm; 