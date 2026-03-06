import React from "react";
import type { GatsbySSR } from "gatsby";

/**
 * Blocking script to set theme BEFORE first paint
 * Prevents flash of wrong theme during hydration
 */
const ThemeScript = () => {
  const script = `
(function() {
  var d = document.documentElement;
  d.classList.add('no-transition');
  try {
    var theme = localStorage.getItem('swarmit-theme');
    var parsed = theme ? JSON.parse(theme) : 'auto';
    var resolved = parsed;
    if (parsed === 'auto') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    d.classList.remove('light', 'dark');
    d.classList.add(resolved);
  } catch (e) {
    d.classList.add('light');
  }
  setTimeout(function() { d.classList.remove('no-transition'); }, 100);
})();
`;
  return <script dangerouslySetInnerHTML={{ __html: script }} />;
};

export const onRenderBody: GatsbySSR["onRenderBody"] = ({
  setHeadComponents,
  setPreBodyComponents,
  setHtmlAttributes,
}) => {
  // Set default theme class
  setHtmlAttributes({ className: "light" });

  // Inject blocking theme script before body
  setPreBodyComponents([<ThemeScript key="theme-script" />]);

  // Font preloading
  setHeadComponents([
    <link
      key="preconnect-google-fonts"
      rel="preconnect"
      href="https://fonts.googleapis.com"
    />,
    <link
      key="preconnect-gstatic"
      rel="preconnect"
      href="https://fonts.gstatic.com"
      crossOrigin="anonymous"
    />,
    <link
      key="google-fonts"
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@600;700&display=swap"
      rel="stylesheet"
    />,
  ]);
};
