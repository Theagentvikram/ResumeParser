import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, Check, Clock, X, FileText } from "lucide-react";
import axios from "axios";
import { API_ENDPOINTS, API_BASE_URL } from "@/config/api";
import { formatRelativeDate } from "@/lib/utils";

// Resume type definition
type Resume = {
  id: string;
  filename: string;
  originalName?: string;
  downloadUrl?: string;
  upload_date: string;
  status?: string;
  match_score?: number;
  summary?: string;
  skills?: string[];
  experience?: number | string;
  educationLevel?: string;
  category?: string;
};

const ResumeDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch resume details
  useEffect(() => {
    const fetchResumeDetails = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        // First try to get from local storage
        const storedResumes = localStorage.getItem("resumatch_user_resumes");
        if (storedResumes) {
          const parsedResumes = JSON.parse(storedResumes);
          const foundResume = parsedResumes.find((r: any) => r.id === id);
          if (foundResume) {
            console.log("Found resume in localStorage:", foundResume);
            setResume(foundResume);
            setLoading(false);
            return;
          }
        }
        
        // If not in localStorage, try to fetch from API
        const response = await axios.get(`${API_ENDPOINTS.RESUME.GET_ALL}`);
        const allResumes = response.data;
        const foundResume = allResumes.find((r: any) => r.id === id);
        
        if (foundResume) {
          // Map API response to our Resume type
          const mappedResume = {
            id: foundResume.id,
            filename: foundResume.filename || "Resume",
            originalName: foundResume.filename,
            downloadUrl: foundResume.download_url,
            upload_date: foundResume.upload_date,
            status: foundResume.status || "pending",
            match_score: foundResume.match_score || 0,
            summary: foundResume.summary || "",
            skills: foundResume.skills || [],
            experience: typeof foundResume.experience === 'string' ? 
              parseInt(foundResume.experience) : foundResume.experience || 0,
            educationLevel: foundResume.educationLevel || "",
            category: foundResume.category || ""
          };
          
          setResume(mappedResume);
        } else {
          setError("Resume not found");
        }
      } catch (err) {
        console.error("Error fetching resume details:", err);
        setError("Failed to load resume details");
      } finally {
        setLoading(false);
      }
    };

    fetchResumeDetails();
  }, [id]);

  // Helper function to get status icon
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

  // Helper function to get status text
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

  // Helper function to download resume
  const downloadResume = () => {
    if (resume?.id) {
      const downloadUrl = `${API_BASE_URL}/resumes/download/${resume.id}`;
      console.log("Downloading resume from:", downloadUrl);
      window.open(downloadUrl, "_blank");
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="container py-8 max-w-4xl mx-auto">
          <div className="flex items-center mb-6">
            <Button 
              variant="ghost" 
              className="mr-4"
              onClick={() => navigate("/upload-status")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" /> Back
            </Button>
            <h1 className="text-2xl font-bold text-white">Resume Details</h1>
          </div>
          <div className="text-center py-8">
            <div className="animate-spin h-8 w-8 border-t-2 border-blue-500 border-r-2 rounded-full mx-auto mb-4"></div>
            <p className="text-gray-400">Loading resume details...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !resume) {
    return (
      <Layout>
        <div className="container py-8 max-w-4xl mx-auto">
          <div className="flex items-center mb-6">
            <Button 
              variant="ghost" 
              className="mr-4"
              onClick={() => navigate("/upload-status")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" /> Back
            </Button>
            <h1 className="text-2xl font-bold text-white">Resume Details</h1>
          </div>
          <div className="p-6 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
            <X className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <h3 className="text-lg font-medium text-white mb-2">Error Loading Resume</h3>
            <p className="text-gray-400 mb-4">{error || "Resume not found"}</p>
            <Button 
              onClick={() => navigate("/upload-status")}
              variant="outline"
              className="border-white/20 hover:bg-white/10"
            >
              Back to Resumes
            </Button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container py-8 max-w-4xl mx-auto">
        <div className="flex items-center mb-6">
          <Button 
            variant="ghost" 
            className="mr-4"
            onClick={() => navigate("/upload-status")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" /> Back
          </Button>
          <h1 className="text-2xl font-bold text-white">Resume Details</h1>
        </div>

        <Card className="backdrop-blur-sm bg-white/5 border-white/10 overflow-hidden">
          <CardHeader className="pb-2 border-b border-white/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="h-6 w-6 text-purple-400" />
                <CardTitle className="text-white text-xl">
                  {resume.originalName || resume.filename}
                </CardTitle>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/5">
                {getStatusIcon(resume.status)}
                <span className="text-sm font-medium">
                  {getStatusText(resume.status)}
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center mt-2">
              <p className="text-sm text-gray-400">
                Uploaded {formatRelativeDate(resume.upload_date)}
              </p>
              <Button 
                variant="outline" 
                size="sm" 
                className="text-xs border-white/20 hover:bg-white/10"
                onClick={downloadResume}
              >
                <Download className="h-3 w-3 mr-1" /> Download
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* Match Score */}
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Match Score</h3>
                <div className="flex items-center">
                  <div className="w-full bg-gray-700 rounded-full h-4">
                    <div 
                      className={`h-4 rounded-full ${
                        (resume.match_score || 0) > 70 ? "bg-green-500" :
                        (resume.match_score || 0) > 50 ? "bg-yellow-500" : "bg-red-500"
                      }`}
                      style={{ width: `${resume.match_score || 0}%` }}
                    ></div>
                  </div>
                  <span className={`ml-3 font-bold ${
                    (resume.match_score || 0) > 70 ? "text-green-400" :
                    (resume.match_score || 0) > 50 ? "text-yellow-400" : "text-red-400"
                  }`}>
                    {resume.match_score !== undefined && resume.match_score !== null ? `${resume.match_score}%` : 'N/A'}
                  </span>
                </div>
              </div>
              
              {/* Summary */}
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Summary</h3>
                <p className="text-gray-300">
                  {resume.summary || "No summary available"}
                </p>
              </div>
              
              {/* Skills */}
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {resume.skills && resume.skills.length > 0 ? (
                    resume.skills.map((skill, index) => (
                      <Badge key={index} className="bg-purple-500/20 text-purple-300 hover:bg-purple-500/30">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-gray-400">No skills listed</p>
                  )}
                </div>
              </div>
              
              {/* Experience & Education */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-2">Experience</h3>
                  <p className="text-gray-300">
                    {resume.experience ? `${resume.experience} years` : "Not specified"}
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white mb-2">Education</h3>
                  <p className="text-gray-300">
                    {resume.educationLevel || "Not specified"}
                  </p>
                </div>
              </div>
              
              {/* Category */}
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Category</h3>
                <Badge className="bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 px-3 py-1">
                  {resume.category || "Uncategorized"}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default ResumeDetailsPage;
