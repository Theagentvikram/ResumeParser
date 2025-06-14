import { ReactNode } from "react";
import { Navbar } from "@/components/Navbar";
import { motion } from "framer-motion";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#0a0a1b] via-[#1a1a3a] to-[#32235c]">
      <Navbar />
      <motion.main 
        className="flex-1 container mx-auto p-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {children}
      </motion.main>
      <footer className="backdrop-blur-sm border-t border-white/10 py-4 px-6 text-center text-sm text-gray-300">
        <div className="container mx-auto">
          <motion.div 
            className="flex flex-col md:flex-row justify-between items-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-2 md:mb-0">
              ResuMatch &copy; {new Date().getFullYear()} - Smart Resume Selection Platform
            </div>
            <div className="flex space-x-4">
              <a href="#" className="hover:text-brand-blue transition-colors">Terms</a>
              <a href="#" className="hover:text-brand-blue transition-colors">Privacy</a>
              <a href="#" className="hover:text-brand-blue transition-colors">Support</a>
            </div>
          </motion.div>
        </div>
      </footer>
    </div>
  );
}
