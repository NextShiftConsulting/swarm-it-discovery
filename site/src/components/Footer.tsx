import React from "react";

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-brand">
          <span className="logo-text">Next Shift Consulting</span>
          <p className="tagline">AI-Powered Research Discovery</p>
        </div>

        <div className="footer-section">
          <h4>Swarm-It Research</h4>
          <ul>
            <li><a href="/">Latest Discoveries</a></li>
            <li><a href="/papers">Paper Archive</a></li>
            <li><a href="/topics">Research Topics</a></li>
            <li><a href="/methodology">Our Methodology</a></li>
          </ul>
        </div>

        <div className="footer-section">
          <h4>Topics We Track</h4>
          <ul>
            <li>Representation Learning</li>
            <li>Multi-Agent Systems</li>
            <li>AI Safety & Alignment</li>
            <li>Neural-Symbolic Integration</li>
          </ul>
        </div>

        <div className="footer-section">
          <h4>Connect</h4>
          <ul>
            <li><a href="https://nextshiftconsulting.com/contact">Contact Us</a></li>
            <li><a href="https://github.com/nextshift">GitHub</a></li>
            <li><a href="/rss.xml">RSS Feed</a></li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; {currentYear} Next Shift Consulting. All rights reserved.</p>
        <p className="powered-by">
          Powered by <a href="https://github.com/nextshift/swarm-it">Swarm-It</a> RSCT Certification
        </p>
      </div>
    </footer>
  );
};

export default Footer;
