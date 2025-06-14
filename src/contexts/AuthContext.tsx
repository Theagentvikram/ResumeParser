import { createContext, useState, useContext, useEffect, ReactNode } from "react";
import { User } from "@/types";
import { getUserFromStorage } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { loginUser as mockLoginUser } from "@/lib/mockData";

interface AuthContextType {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  userType: "recruiter" | "applicant" | null;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userType, setUserType] = useState<"recruiter" | "applicant" | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Check for existing user session on mount
  useEffect(() => {
    const storedUser = getUserFromStorage();
    
    if (storedUser) {
      setUser(storedUser);
      setUserType(storedUser.role === "admin" || storedUser.role === "recruiter" ? "recruiter" : "applicant");
    }
    
    setIsLoading(false);
  }, []);

  // For demo purposes, directly set the user without API calls
  const login = (user: User) => {
    setUser(user);
    
    // Set user type based on role
    const type = user.role === "admin" || user.role === "recruiter" ? "recruiter" : "applicant";
    setUserType(type);
    
    // Save to localStorage
    localStorage.setItem("resumatch_user", JSON.stringify(user));
    localStorage.setItem("resumatch_token", "mock-token-" + Date.now());
  };

  const logout = () => {
    setUser(null);
    setUserType(null);
    
    // Clear from localStorage
    localStorage.removeItem("resumatch_user");
    localStorage.removeItem("resumatch_token");
    
    toast({
      title: "Logged out",
      description: "You have been successfully logged out.",
    });
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    userType,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
