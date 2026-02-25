import React from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";
import "../styles/globals.css";

interface LayoutProps {
  children: React.ReactNode;
  pageTitle?: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, pageTitle }) => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      {/* Add padding-top to account for fixed header */}
      <main className="flex-1 pt-16">
        {pageTitle && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl lg:text-4xl font-bold text-gray-900">{pageTitle}</h1>
          </div>
        )}
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
