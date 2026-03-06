module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  env: {
    browser: true,
    node: true,
    es2022: true,
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  plugins: ['@typescript-eslint', 'react', 'react-hooks'],
  rules: {
    // React 17+ JSX transform doesn't require React import
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off', // Using TypeScript for prop types

    // TypeScript handles these
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',

    // Allow unused vars with underscore prefix
    '@typescript-eslint/no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    }],

    // React Hooks rules
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',

    // Code quality
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'prefer-const': 'error',
    'no-var': 'error',
  },
  ignorePatterns: [
    'node_modules/',
    'public/',
    '.cache/',
    'gatsby-*.js',
    '*.config.js',
  ],
};
