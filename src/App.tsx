import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ResumeProvider } from "@/contexts/ResumeContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { logEnvConfig, checkBackendConnection } from "@/utils/debug";
import { useEffect } from "react";

// Pages
import Index from "./pages/Index";
import LoginPage from "./pages/LoginPage";
import RecruiterLoginPage from "./pages/RecruiterLoginPage";
import UserLoginPage from "./pages/UserLoginPage";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import UploadStatusPage from "./pages/UploadStatusPage";
import ResumeDetailsPage from "./pages/ResumeDetailsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Global query error handler
queryClient.getQueryCache().config.onError = (error) => {
  console.error('React Query Error:', error);
};

interface DebugWrapperProps {
  children: React.ReactNode;
}

const DebugWrapper: React.FC<DebugWrapperProps> = ({ children }) => {
  useEffect(() => {
    // Log environment configuration
    logEnvConfig();
    
    // Check backend connection
    checkBackendConnection().then(isConnected => {
      console.log(`Backend is ${isConnected ? 'connected' : 'not reachable'}`);
    });
  }, []);

  return children;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <ResumeProvider>
          <DebugWrapper>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Index />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/recruiter-login" element={<RecruiterLoginPage />} />
              <Route path="/user-login" element={<UserLoginPage />} />
              
              {/* Applicant Routes */}
              <Route 
                path="/upload" 
                element={
                  <ProtectedRoute requiredUserType="applicant">
                    <UploadPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/upload-status" 
                element={
                  <ProtectedRoute requiredUserType="applicant">
                    <UploadStatusPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/resume/:id" 
                element={
                  <ProtectedRoute requiredUserType="applicant">
                    <ResumeDetailsPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Recruiter Routes */}
              <Route 
                path="/search" 
                element={
                  <ProtectedRoute requiredUserType="recruiter">
                    <SearchPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* 404 Route */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </DebugWrapper>
        </ResumeProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
