import React from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";
import "../styles/global.css";

interface LayoutProps {
  children: React.ReactNode;
  pageTitle?: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, pageTitle }) => {
  return (
    <div className="site-wrapper">
      <Header />
      <main className="main-content">
        {pageTitle && <h1 className="page-title">{pageTitle}</h1>}
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
