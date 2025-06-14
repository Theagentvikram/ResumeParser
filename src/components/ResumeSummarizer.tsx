import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Brain, Loader2, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { analyzeResume } from "@/lib/api";

interface ResumeSummarizerProps {
  resumeText?: string;
  onSummaryComplete?: (summary: {
    skills: string[];
    experience: number;
    educationLevel: string;
    summary: string;
    category: string;
  }) => void;
}

export function ResumeSummarizer({ resumeText = "", onSummaryComplete }: ResumeSummarizerProps) {
  const [text, setText] = useState(resumeText);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [summary, setSummary] = useState<{
    skills: string[];
    experience: number;
    educationLevel: string;
    summary: string;
    category: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyzeResume = async () => {
    if (!text.trim()) {
      setError("Please enter resume text to analyze");
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    
    try {
      // Use the improved analyzeResume API function
      const result = await analyzeResume(text);
      
      setSummary(result);
      
      if (onSummaryComplete) {
        onSummaryComplete(result);
      }
    } catch (err) {
      setError("Failed to analyze resume. Please try again.");
      console.error("Resume analysis error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={{ boxShadow: "0 10px 30px -15px rgba(124, 58, 237, 0.3)" }}
      className="transition-all duration-300"
    >
      <Card className="w-full backdrop-blur-sm bg-white/5 border-white/10 border overflow-hidden relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
        <CardHeader className="relative z-10">
          <CardTitle className="flex items-center gap-2 text-white">
            <motion.div
              animate={{ rotate: [0, 5, 0, -5, 0] }}
              transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
            >
              <Brain className="h-5 w-5 text-purple-400" />
            </motion.div>
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 text-transparent bg-clip-text">AI Resume Analyzer</span>
          </CardTitle>
          <CardDescription className="text-gray-400">
            Use our AI-powered tool to automatically extract key information from resumes
          </CardDescription>
        </CardHeader>
        <CardContent className="relative z-10">
          {!summary ? (
            <motion.div 
              className="space-y-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Textarea
                placeholder="Paste resume text here or upload a resume file..."
                className="min-h-[200px] bg-white/5 border-white/10 resize-none focus:border-purple-500 hover:border-purple-400/50 transition-all duration-300"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              {error && (
                <motion.div 
                  className="flex items-center gap-2 text-red-400 text-sm"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <AlertTriangle className="h-4 w-4" />
                  {error}
                </motion.div>
              )}
            </motion.div>
          ) : (
            <motion.div 
              className="space-y-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <div className="space-y-3">
                <motion.div 
                  className="flex justify-between items-center"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.1 }}
                >
                  <h3 className="text-sm font-medium text-gray-300">Job Category</h3>
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-300/20 group-hover:bg-purple-500/30 transition-colors duration-300">
                    {summary.category}
                  </Badge>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                >
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Summary</h3>
                  <p className="text-sm text-gray-400 bg-white/5 p-3 rounded-md border border-white/10 group-hover:border-purple-500/20 transition-all duration-300">
                    {summary.summary}
                  </p>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                >
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {summary.skills.map((skill, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: 0.3 + (i * 0.05) }}
                        whileHover={{ y: -3, scale: 1.05 }}
                      >
                        <Badge className="bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-all duration-300">
                          {skill}
                        </Badge>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
                
                <div className="grid grid-cols-2 gap-4">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.4 }}
                    whileHover={{ y: -3 }}
                  >
                    <h3 className="text-sm font-medium text-gray-300 mb-2">Experience</h3>
                    <div className="text-sm text-gray-400 bg-white/5 p-3 rounded-md border border-white/10 group-hover:border-blue-500/20 transition-all duration-300">
                      {summary.experience} years
                    </div>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.5 }}
                    whileHover={{ y: -3 }}
                  >
                    <h3 className="text-sm font-medium text-gray-300 mb-2">Education</h3>
                    <div className="text-sm text-gray-400 bg-white/5 p-3 rounded-md border border-white/10 group-hover:border-green-500/20 transition-all duration-300">
                      {summary.educationLevel}
                    </div>
                  </motion.div>
                </div>
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.6 }}
                whileHover={{ y: -3 }}
              >
                <Button 
                  variant="outline" 
                  className="w-full border-white/10 hover:bg-white/10 text-gray-300 hover:text-white group-hover:border-purple-500/30 transition-all duration-300"
                  onClick={() => {
                    setSummary(null);
                    setText("");
                  }}
                >
                  Analyze Another Resume
                </Button>
              </motion.div>
            </motion.div>
          )}
        </CardContent>
        {!summary && (
          <CardFooter className="flex justify-between border-t border-white/10 pt-4 relative z-10">
            <motion.div 
              className="text-xs text-gray-400 group-hover:text-gray-300 transition-colors duration-300"
              animate={{ opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              AI-powered resume analysis
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                onClick={handleAnalyzeResume} 
                disabled={isAnalyzing}
                className="relative overflow-hidden group/button bg-gradient-to-r from-purple-500 to-purple-700 hover:opacity-90"
              >
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-purple-400 to-purple-600 opacity-0 group-hover/button:opacity-100 transition-opacity duration-300 blur-lg"></div>
                <div className="relative z-10">
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain className="mr-2 h-4 w-4" />
                      Analyze Resume
                    </>
                  )}
                </div>
              </Button>
            </motion.div>
          </CardFooter>
        )}
      </Card>
    </motion.div>
  );
} 