import React from "react";

interface NavLink {
  label: string;
  href: string;
  external?: boolean;
}

const mainSiteLinks: NavLink[] = [
  { label: "Home", href: "https://nextshiftconsulting.com", external: true },
  { label: "Services", href: "https://nextshiftconsulting.com/services", external: true },
  { label: "Research", href: "/", external: false },
  { label: "Blog", href: "https://nextshiftconsulting.com/blog", external: true },
  { label: "Contact", href: "https://nextshiftconsulting.com/contact", external: true },
];

const subLinks: NavLink[] = [
  { label: "Discoveries", href: "/" },
  { label: "Papers", href: "/papers" },
  { label: "Topics", href: "/topics" },
  { label: "About", href: "/about" },
];

export const Header: React.FC = () => {
  return (
    <header className="site-header">
      {/* Main navigation - matches nextshiftconsulting.com */}
      <nav className="main-nav">
        <div className="nav-container">
          <a href="https://nextshiftconsulting.com" className="logo">
            <span className="logo-text">Next Shift</span>
            <span className="logo-accent">Consulting</span>
          </a>
          <ul className="nav-links">
            {mainSiteLinks.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  className={link.label === "Research" ? "active" : ""}
                  {...(link.external ? { target: "_blank", rel: "noopener" } : {})}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* Sub-navigation for swarmit section */}
      <nav className="sub-nav">
        <div className="nav-container">
          <div className="section-title">
            <span className="swarm-badge">Swarm-It</span>
            <span>Research Discovery</span>
          </div>
          <ul className="sub-links">
            {subLinks.map((link) => (
              <li key={link.href}>
                <a href={link.href}>{link.label}</a>
              </li>
            ))}
          </ul>
        </div>
      </nav>
    </header>
  );
};

export default Header;
