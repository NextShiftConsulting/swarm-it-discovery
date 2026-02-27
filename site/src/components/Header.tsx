import React, { useState } from "react";
import { Link } from "gatsby";
import { LogoColor } from "./Logo";
import { ThemeToggle } from "./ui/ThemeToggle";

interface NavLink {
  label: string;
  to: string;
  external?: boolean;
}

interface DropdownNavLink extends NavLink {
  dropdown?: NavLink[];
}

const navItems: DropdownNavLink[] = [
  { label: "Home", to: "https://nextshiftconsulting.com", external: true },
  {
    label: "Services",
    to: "https://nextshiftconsulting.com/services",
    external: true,
    dropdown: [
      { label: "All Services", to: "https://nextshiftconsulting.com/services", external: true },
      { label: "Quality Audits", to: "https://nextshiftconsulting.com/services/context-quality-audits/", external: true },
      { label: "Validation & Testing", to: "https://nextshiftconsulting.com/services/model-validation-testing/", external: true },
      { label: "YRSN Integration", to: "https://nextshiftconsulting.com/services/yrsn-integration/", external: true },
    ],
  },
  { label: "Research", to: "/" },
  { label: "Blog", to: "https://nextshiftconsulting.com/blog", external: true },
];

export const Header: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileDropdownOpen, setMobileDropdownOpen] = useState<string | null>(null);

  const renderLink = (item: NavLink, className: string, children: React.ReactNode, onClick?: () => void) => {
    if (item.external) {
      return (
        <a
          href={item.to}
          className={className}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClick}
        >
          {children}
        </a>
      );
    }
    return (
      <Link to={item.to} className={className} onClick={onClick}>
        {children}
      </Link>
    );
  };

  return (
    <nav className="fixed w-full z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo + Text */}
          <a
            href="https://nextshiftconsulting.com"
            className="flex items-center gap-3 hover:opacity-90 transition-opacity"
          >
            <LogoColor className="h-10 w-10" />
            <span className="text-xl font-bold font-heading">
              <span className="text-gray-800">Next Shift</span>{" "}
              <span className="text-amber-600">Consulting</span>
            </span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-6">
            {navItems.map((item) => (
              <div
                key={item.label}
                className="relative"
                onMouseEnter={() => item.dropdown && setActiveDropdown(item.label)}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                {renderLink(
                  item,
                  `font-medium text-gray-700 hover:text-blue-600 transition-colors py-2 flex items-center ${item.label === "Research" ? "text-blue-600" : ""}`,
                  <>
                    {item.label}
                    {item.dropdown && (
                      <svg
                        className={`w-4 h-4 ml-1 transition-transform ${activeDropdown === item.label ? "rotate-180" : ""}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    )}
                  </>
                )}

                {/* Dropdown Menu */}
                {item.dropdown && activeDropdown === item.label && (
                  <div className="absolute top-full left-0 pt-2 w-56 z-50">
                    <div className="bg-white rounded-xl shadow-lg border border-gray-200 py-2">
                      {item.dropdown.map((subItem) =>
                        renderLink(
                          subItem,
                          "block px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors",
                          subItem.label
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* CTA Button */}
            <a
              href="https://nextshiftconsulting.com/contact"
              className="bg-blue-600 text-white px-6 py-2 rounded-full font-bold hover:bg-blue-700 transition-colors"
            >
              Contact
            </a>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={isOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
              />
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="lg:hidden py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 max-h-[80vh] overflow-y-auto">
            <div className="flex flex-col space-y-1">
              {navItems.map((item) => (
                <div key={item.label}>
                  {item.dropdown ? (
                    <>
                      <button
                        onClick={() =>
                          setMobileDropdownOpen(
                            mobileDropdownOpen === item.label ? null : item.label
                          )
                        }
                        className="w-full flex items-center justify-between py-3 px-3 font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        <span>{item.label}</span>
                        <svg
                          className={`w-5 h-5 transition-transform ${mobileDropdownOpen === item.label ? "rotate-180" : ""}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {mobileDropdownOpen === item.label && (
                        <div className="ml-3 pl-3 border-l-2 border-blue-200 space-y-1 mb-2">
                          {item.dropdown.map((subItem) =>
                            renderLink(
                              subItem,
                              "block py-2.5 px-3 text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors",
                              subItem.label,
                              () => setIsOpen(false)
                            )
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    renderLink(
                      item,
                      `block py-3 px-3 font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors ${item.label === "Research" ? "text-blue-600" : ""}`,
                      item.label,
                      () => setIsOpen(false)
                    )
                  )}
                </div>
              ))}

              {/* Theme Toggle for Mobile */}
              <div className="flex items-center justify-between py-3 px-3">
                <span className="font-medium text-gray-700 dark:text-gray-300">Theme</span>
                <ThemeToggle />
              </div>

              <a
                href="https://nextshiftconsulting.com/contact"
                className="mt-4 mx-2 text-center bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition-colors"
                onClick={() => setIsOpen(false)}
              >
                Contact
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Header;
