import React from "react";
import { Link } from "gatsby";
import { LogoWhite } from "./Logo";

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  const quickLinks = [
    { label: "Latest Reviews", to: "/" },
    { label: "Topics", to: "/topics" },
    { label: "About", to: "/about" },
  ];

  const mainSiteLinks = [
    { label: "Services", to: "https://nextshiftconsulting.com/services", external: true },
    { label: "Blog", to: "https://nextshiftconsulting.com/blog", external: true },
    { label: "Contact", to: "https://nextshiftconsulting.com/contact", external: true },
  ];

  const legalLinks = [
    { label: "Privacy Policy", to: "https://nextshiftconsulting.com/privacy/", external: true },
    { label: "Terms of Service", to: "https://nextshiftconsulting.com/terms/", external: true },
  ];

  const socialLinks = [
    {
      name: "Contact",
      url: "https://nextshiftconsulting.com/contact",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      color: "hover:bg-blue-500 hover:text-white",
    },
    {
      name: "GitHub",
      url: "https://github.com/nextshift",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/>
        </svg>
      ),
      color: "hover:bg-gray-700 hover:text-white",
    },
  ];

  return (
    <footer className="bg-gray-900 text-gray-300" role="contentinfo">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <a href="https://nextshiftconsulting.com" className="inline-block mb-4">
              <LogoWhite className="h-28 w-28" />
            </a>
            <h2 className="text-xl font-bold mb-4 font-heading">
              <span className="text-white">Next Shift</span>{" "}
              <span className="text-amber-400">Consulting</span>
            </h2>
            <p className="mb-6 max-w-md text-gray-400 leading-relaxed">
              AI-curated research discovery powered by Swarm-It RSCT certification.
            </p>

            {/* Social Links */}
            <div className="flex space-x-3 mb-6" aria-label="Social media links">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`w-12 h-12 bg-white/10 border border-gray-700 text-gray-300 rounded-lg flex items-center justify-center transition-all duration-300 ${social.color} hover:-translate-y-1 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900`}
                  aria-label={`Visit our ${social.name} page (opens in new tab)`}
                >
                  <span className="sr-only">{social.name}</span>
                  {social.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Research Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">
              Research Discovery
            </h3>
            <nav aria-label="Research navigation">
              <ul className="space-y-3">
                {quickLinks.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.to}
                      className="block text-gray-400 hover:text-blue-400 transition-colors focus:outline-none focus:text-blue-400"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          {/* Main Site Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">
              Next Shift Consulting
            </h3>
            <nav aria-label="Main site navigation">
              <ul className="space-y-3">
                {mainSiteLinks.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.to}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-gray-400 hover:text-blue-400 transition-colors focus:outline-none focus:text-blue-400"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </div>

        {/* Legal Links & Copyright */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <nav aria-label="Legal links">
              <ul className="flex flex-wrap justify-center gap-4 md:gap-6">
                {legalLinks.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.to}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-500 hover:text-blue-400 transition-colors text-sm focus:outline-none focus:text-blue-400"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
            <p className="text-gray-500 text-sm text-center md:text-right">
              © {currentYear} Next Shift Consulting. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
