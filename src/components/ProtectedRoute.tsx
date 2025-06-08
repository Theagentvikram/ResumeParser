import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "admin" | "recruiter" | "applicant";
  requiredUserType?: "recruiter" | "applicant";
}

export function ProtectedRoute({ children, requiredRole, requiredUserType }: ProtectedRouteProps) {
  const { isAuthenticated, user, userType } = useAuth();

  // If not authenticated, redirect to appropriate login page
  if (!isAuthenticated) {
    if (requiredUserType === "recruiter") {
      return <Navigate to="/recruiter-login" replace />;
    } else if (requiredUserType === "applicant") {
      return <Navigate to="/user-login" replace />;
    } else {
      return <Navigate to="/login" replace />;
    }
  }

  // If authenticated but wrong role/user type for the page
  if (user) {
    // For pages that require specific roles
    if (requiredRole && user.role !== requiredRole) {
      if (user.role === "admin" || user.role === "recruiter") {
        return <Navigate to="/search" replace />;
      } else {
        return <Navigate to="/upload-status" replace />;
      }
    }

    // For pages that require specific user types
    if (requiredUserType && userType !== requiredUserType) {
      if (userType === "recruiter") {
        return <Navigate to="/search" replace />;
      } else if (userType === "applicant") {
        return <Navigate to="/upload-status" replace />;
      }
    }
  }

  return <>{children}</>;
}
