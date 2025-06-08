import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useResumes } from "@/contexts/ResumeContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Download, Clock, Check, X } from "lucide-react";
import { formatRelativeDate } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";

// Define a more flexible Resume type that can handle both API and context data
type Resume = {
  id: string;
  filename: string;
  originalName?: string;
  downloadUrl?: string;
  upload_date?: string;
  uploadDate?: string; // From context
  status?: string;
  match_score?: number;
  matchScore?: number; // From context
  summary?: string;
  skills?: string[];
  experience?: number | string;
  educationLevel?: string;
  category?: string;
};

export function ResumeDisplay() {
  const [localResumes, setLocalResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const { resumes: contextResumes, loadUserResumes } = useResumes();

  // Function to fetch resumes directly from the API
  const fetchResumes = useCallback(async () => {
    setLoading(true);
    console.log("Fetching resumes directly from API");
    try {
      // First try to use the context's loadUserResumes function
      try {
        if (typeof loadUserResumes === 'function') {
          await loadUserResumes();
          // After loading, check if we have resumes in the context
          if (contextResumes && contextResumes.length > 0) {
            console.log("Using resumes from context:", contextResumes);
            // Explicitly map context resumes to our local type
            const mappedResumes = contextResumes.map(r => ({
              id: r.id,
              filename: r.filename || r.name || 'resume.pdf',
              originalName: r.originalName || r.name,
              downloadUrl: r.downloadUrl,
              upload_date: r.uploadDate || new Date().toISOString(),
              status: r.status || 'pending',
              match_score: r.matchScore || 0,
              summary: r.summary || '',
              skills: r.skills || [],
              experience: r.experience || 0,
              educationLevel: r.educationLevel || '',
              category: r.category || ''
            }));
            setLocalResumes(mappedResumes);
            setError(null);
            setLoading(false);
            return;
          }
        }
      } catch (contextError) {
        console.error("Error loading from context:", contextError);
        // Continue to direct API call
      }
      
      // Fallback to direct API call if context method fails or returns empty
      const response = await axios.get("http://localhost:8000/resumes");
      console.log("Direct API Response:", response.data);
      setLocalResumes(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching resumes:", err);
      setError("Failed to load resumes. Please try again.");
      toast({
        title: "Error",
        description: "Failed to load resumes. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [loadUserResumes, toast]);

  // Check for 'new' parameter in URL to force immediate refresh
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const newUpload = urlParams.get('new');
    
    if (newUpload) {
      console.log("New upload detected, refreshing immediately");
      fetchResumes();
      
      // Clear the URL parameter after handling it
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
      
      toast({
        title: "Resume Uploaded",
        description: "Your resume has been uploaded and is being processed.",
      });
    }
  }, []);

  // Watch for changes in the context resumes
  useEffect(() => {
    if (contextResumes && contextResumes.length > 0) {
      console.log("Context resumes updated, refreshing display", contextResumes);
      // Explicitly map context resumes to our local type
      const mappedResumes = contextResumes.map(r => ({
        id: r.id,
        filename: r.filename || r.name || 'resume.pdf',
        originalName: r.originalName || r.name,
        downloadUrl: r.downloadUrl,
        upload_date: r.uploadDate || new Date().toISOString(),
        status: r.status || 'pending',
        match_score: r.matchScore || 0,
        summary: r.summary || '',
        skills: r.skills || [],
        experience: r.experience || 0,
        educationLevel: r.educationLevel || '',
        category: r.category || ''
      }));
      setLocalResumes(mappedResumes);
    }
  }, [contextResumes]);

  // Load resumes on component mount and set up polling
  useEffect(() => {
    console.log("Setting up resume polling");
    fetchResumes();
    
    // Poll more frequently initially (every 2 seconds for the first 30 seconds)
    const fastPollingId = setInterval(fetchResumes, 2000);
    
    // After 30 seconds, switch to slower polling
    const slowPollingTimeoutId = setTimeout(() => {
      clearInterval(fastPollingId);
      const slowPollingId = setInterval(fetchResumes, 10000); // Every 10 seconds
      
      return () => clearInterval(slowPollingId);
    }, 30000);
    
    // Set up a custom event listener for resume uploads
    const handleResumeUploaded = () => {
      console.log("Resume uploaded event detected, refreshing immediately");
      fetchResumes();
      toast({
        title: "Resume Uploaded",
        description: "Your resume has been uploaded and is being processed.",
      });
    };
    
    // Listen for a custom event that will be dispatched when a resume is uploaded
    window.addEventListener('resumeUploaded', handleResumeUploaded);
    
    // Clean up all intervals, timeouts, and event listeners on unmount
    return () => {
      clearInterval(fastPollingId);
      clearTimeout(slowPollingTimeoutId);
      window.removeEventListener('resumeUploaded', handleResumeUploaded);
    };
  }, [fetchResumes]);

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "reviewed":
      case "processed":
        return <Check className="h-5 w-5 text-green-500" />;
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case "rejected":
        return <X className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case "reviewed":
      case "processed":
        return "Processed";
      case "pending":
        return "Under Review";
      case "rejected":
        return "Not a Match";
      default:
        return "Processing";
    }
  };

  const downloadResume = (resume: Resume) => {
    if (resume.downloadUrl) {
      window.open(resume.downloadUrl, "_blank");
    }
  };

  const viewDetails = (resume: Resume) => {
    toast({
      title: "Resume Details",
      description: `Viewing details for ${resume.filename}`,
    });
    // Open in a new tab with JSON data
    const jsonData = JSON.stringify(resume, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  // Refresh button handler
  const handleRefresh = () => {
    fetchResumes();
    toast({
      title: "Refreshing",
      description: "Fetching the latest resumes...",
    });
  };

  if (loading && localResumes.length === 0) {
    return <div className="text-center py-8">Loading resumes...</div>;
  }

  if (error && localResumes.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500 mb-4">{error}</p>
        <Button onClick={handleRefresh}>Try Again</Button>
      </div>
    );
  }

  if (localResumes.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-400 mb-4">No resumes found. Upload a resume to get started.</p>
        <Button onClick={handleRefresh}>Refresh</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end mb-4">
        <Button onClick={handleRefresh} variant="outline" className="text-sm">
          Refresh Resumes
        </Button>
      </div>
      
      {localResumes.map((resume) => (
        <Card key={resume.id} className="backdrop-blur-sm bg-white/5 border-white/10 hover:bg-white/10 transition-all duration-300">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-400" />
                <CardTitle className="text-white">{resume.originalName || resume.filename}</CardTitle>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/5">
                {getStatusIcon(resume.status)}
                <span className="text-sm font-medium">
                  {getStatusText(resume.status)}
                </span>
              </div>
            </div>
            <CardDescription className="text-gray-400">
              Uploaded {formatRelativeDate(resume.upload_date || resume.uploadDate || new Date().toISOString())}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-300">
                  {resume.status === "pending" ? (
                    "Your resume is being processed"
                  ) : (
                    <>
                      Match Score: 
                      <span className={`ml-2 font-bold ${
                        (resume.match_score || 0) > 70 ? "text-green-400" :
                        (resume.match_score || 0) > 50 ? "text-yellow-400" : "text-red-400"
                      }`}>
                        {resume.match_score !== undefined && resume.match_score !== null ? `${resume.match_score}%` : 'N/A'}
                      </span>
                    </>
                  )}
                </p>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-xs border-white/20 hover:bg-white/10"
                  onClick={() => downloadResume(resume)}
                >
                  <Download className="h-3 w-3 mr-1" /> Download
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-xs border-white/20 hover:bg-white/10"
                  onClick={() => viewDetails(resume)}
                >
                  View Details
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
