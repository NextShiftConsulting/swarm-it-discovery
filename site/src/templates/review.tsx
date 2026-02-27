import React from "react";
import { graphql, PageProps, Link } from "gatsby";
import Layout from "../components/Layout";

interface ReviewData {
  mdx: {
    frontmatter: {
      title: string;
      published_date: string;
      arxiv_id: string;
      kappa: number;
      R: number;
      S: number;
      N: number;
      rsn_score: string;
      abstract: string;
      tldr?: string;
      tags: string[];
      primary_topic: string;
      difficulty: string;
      authors: string[];
      arxiv_url: string;
      pdf_url?: string;
      github_url?: string;
      status: string;
      featured?: boolean;
    };
    fields: {
      qualityTier: string;
      readingTime: number;
      wordCount: number;
    };
  };
}

const ReviewTemplate: React.FC<PageProps<ReviewData>> = ({ data, children }) => {
  const { frontmatter, fields } = data.mdx;

  // Get quality tier color
  const getQualityColor = (tier: string) => {
    const colors: Record<string, string> = {
      exceptional: 'bg-amber-100 text-amber-800',
      'high-quality': 'bg-gray-100 text-gray-800',
      certified: 'bg-orange-100 text-orange-800',
      pending: 'bg-gray-50 text-gray-600'
    };
    return colors[tier] || colors.pending;
  };

  const getDifficultyColor = (difficulty: string) => {
    const colors: Record<string, string> = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-yellow-100 text-yellow-800',
      advanced: 'bg-red-100 text-red-800'
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Layout>
      <article className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Back link */}
          <Link
            to="/"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 mb-8 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to reviews
          </Link>

          {/* Header */}
          <header className="mb-8">
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mb-4">
              <time dateTime={frontmatter.published_date}>{frontmatter.published_date}</time>
              <span className="w-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></span>
              <span>{fields.readingTime} min read</span>
              <span className="w-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></span>
              <a
                href={`https://arxiv.org/abs/${frontmatter.arxiv_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                arXiv:{frontmatter.arxiv_id}
              </a>
            </div>

            <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              {frontmatter.title}
            </h1>

            {frontmatter.authors && frontmatter.authors.length > 0 && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                <strong>Authors:</strong> {frontmatter.authors.join(", ")}
              </p>
            )}

            <div className="flex flex-wrap gap-2 mb-6">
              {/* Quality Tier Badge */}
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getQualityColor(fields.qualityTier)}`}>
                {fields.qualityTier === 'exceptional' && '🥇 '}
                {fields.qualityTier === 'high-quality' && '🥈 '}
                {fields.qualityTier === 'certified' && '🥉 '}
                {fields.qualityTier.charAt(0).toUpperCase() + fields.qualityTier.slice(1)} (κ={frontmatter.kappa.toFixed(2)})
              </span>

              {/* Difficulty Badge */}
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(frontmatter.difficulty)}`}>
                {frontmatter.difficulty.charAt(0).toUpperCase() + frontmatter.difficulty.slice(1)}
              </span>

              {/* Topic Tags */}
              {frontmatter.tags.map(tag => (
                <span key={tag} className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  {tag}
                </span>
              ))}
            </div>

            {/* RSN Breakdown */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">RSCT Score Breakdown</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-600 dark:text-gray-400">Relevance (R)</div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{frontmatter.R.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-gray-600 dark:text-gray-400">Stability (S)</div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{frontmatter.S.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-gray-600 dark:text-gray-400">Novelty (N)</div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{frontmatter.N.toFixed(2)}</div>
                </div>
              </div>
            </div>

            {/* TL;DR */}
            {frontmatter.tldr && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-400 dark:border-amber-600 p-4 mb-6">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">TL;DR</h3>
                <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{frontmatter.tldr}</div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <a
                href={frontmatter.arxiv_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
              >
                Read on arXiv
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>

              {frontmatter.pdf_url && (
                <a
                  href={frontmatter.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center bg-gray-600 dark:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
                >
                  Download PDF
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </a>
              )}

              {frontmatter.github_url && (
                <a
                  href={frontmatter.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center bg-gray-800 dark:bg-gray-900 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-900 dark:hover:bg-gray-800 transition-colors"
                >
                  View Code
                  <svg className="w-4 h-4 ml-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                </a>
              )}
            </div>
          </header>

          {/* Content */}
          <div className="content-area prose prose-lg max-w-none dark:prose-invert">
            {children}
          </div>

          {/* Footer */}
          <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">About This Review</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                This review was auto-generated by the Swarm-It research discovery platform.
                Quality is certified using RSCT (RSN Certificate Technology) with a κ-gate score of {frontmatter.kappa.toFixed(2)}.
                RSN scores: Relevance={frontmatter.R.toFixed(2)}, Stability={frontmatter.S.toFixed(2)}, Novelty={frontmatter.N.toFixed(2)}.
              </p>
            </div>
          </footer>
        </div>
      </article>
    </Layout>
  );
};

export const query = graphql`
  query ReviewPage($id: String!) {
    mdx(id: { eq: $id }) {
      frontmatter {
        title
        published_date(formatString: "MMMM DD, YYYY")
        arxiv_id
        kappa
        R
        S
        N
        rsn_score
        abstract
        tldr
        tags
        primary_topic
        difficulty
        authors
        arxiv_url
        pdf_url
        github_url
        status
        featured
      }
      fields {
        qualityTier
        readingTime
        wordCount
      }
    }
  }
`;

export default ReviewTemplate;
