import React from "react";
import { graphql, PageProps, Link } from "gatsby";
import Layout from "../components/Layout";
import { SearchBox } from "../components/search/SearchBox";

interface DiscoveryNode {
  id: string;
  frontmatter: {
    title: string;
    published_date: string;
    arxiv_id: string;
    kappa: number;
    abstract: string;
    tags: string[];
    difficulty: string;
    featured?: boolean;
  };
  fields: {
    slug: string;
    qualityTier: string;
    readingTime: number;
  };
}

const IndexPage: React.FC<PageProps<{ allMdx: { nodes: DiscoveryNode[] } }>> = ({ data }) => {
  const discoveries = data?.allMdx?.nodes || [];

  const getQualityTierBadge = (tier: string, kappa: number) => {
    const badges = {
      exceptional: { emoji: '🥇', label: 'Exceptional', bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-800 dark:text-amber-200' },
      'high-quality': { emoji: '🥈', label: 'High Quality', bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-200' },
      certified: { emoji: '🥉', label: 'Certified', bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-800 dark:text-orange-200' },
      pending: { emoji: '⏳', label: 'Pending', bg: 'bg-gray-50 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400' }
    };
    const badge = badges[tier as keyof typeof badges] || badges.pending;
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.emoji} κ={kappa.toFixed(2)}
      </span>
    );
  };

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 dark:from-blue-800 dark:via-purple-800 dark:to-gray-900 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl lg:text-5xl font-bold mb-6 font-heading">
              AI Research Discovery
            </h1>
            <p className="text-xl lg:text-2xl text-blue-100 dark:text-blue-200 max-w-3xl mx-auto mb-8">
              RSCT-certified analysis of cutting-edge ML/AI papers.
              Powered by <strong className="text-white">κ-gate quality scoring</strong>.
            </p>
          </div>

          {/* Search Box */}
          <div className="max-w-2xl mx-auto">
            <SearchBox
              placeholder="Search papers by title, abstract, or topic..."
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* Discoveries Section */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Latest Reviews</h2>
            <span className="text-gray-600 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 px-4 py-2 rounded-full text-sm font-medium">
              {discoveries.length} papers reviewed
            </span>
          </div>

          {discoveries.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
              <div className="max-w-md mx-auto">
                <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-600 dark:text-gray-300 text-lg mb-2">No discoveries yet.</p>
                <p className="text-gray-500 dark:text-gray-400">The scanner runs daily, matching papers with RSCT quality certification (κ ≥ 0.7).</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {discoveries.map((node) => (
                <article
                  key={node.id}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
                >
                  {/* Header */}
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                    <time dateTime={node.frontmatter.published_date}>{node.frontmatter.published_date}</time>
                    <span>{node.fields.readingTime} min read</span>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 line-clamp-2">
                    <Link
                      to={node.fields.slug}
                      className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      {node.frontmatter.title}
                    </Link>
                  </h3>

                  {/* Abstract */}
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                    {node.frontmatter.abstract}
                  </p>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2">
                    {getQualityTierBadge(node.fields.qualityTier, node.frontmatter.kappa)}

                    {node.frontmatter.tags.slice(0, 2).map(tag => (
                      <span key={tag} className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* arXiv Link */}
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <a
                      href={`https://arxiv.org/abs/${node.frontmatter.arxiv_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      arXiv:{node.frontmatter.arxiv_id} →
                    </a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center mb-12">How It Works</h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {[
              { step: "1", title: "Daily Scan", desc: "Monitor arXiv for new papers" },
              { step: "2", title: "Match", desc: "Semantic similarity to topics" },
              { step: "3", title: "RSCT Certify", desc: "κ-gate quality scoring (R+S+N)" },
              { step: "4", title: "Publish", desc: "Auto-generate analysis" },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 dark:from-blue-600 dark:to-purple-700 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{item.title}</h3>
                <p className="text-gray-600 dark:text-gray-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">{discoveries.length}</div>
              <div className="text-gray-600 dark:text-gray-400">Papers Reviewed</div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                {discoveries.filter(d => d.frontmatter.kappa >= 0.7).length}
              </div>
              <div className="text-gray-600 dark:text-gray-400">κ-gate Certified (≥0.7)</div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <div className="text-4xl font-bold text-amber-600 dark:text-amber-400 mb-2">
                {discoveries.filter(d => d.frontmatter.kappa >= 0.9).length}
              </div>
              <div className="text-gray-600 dark:text-gray-400">Exceptional Quality</div>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
};

export const query = graphql`
  query {
    allMdx(
      sort: {frontmatter: {published_date: DESC}}
      limit: 20
      filter: {frontmatter: {status: {eq: "live"}}}
    ) {
      nodes {
        id
        frontmatter {
          title
          published_date(formatString: "MMM DD, YYYY")
          arxiv_id
          kappa
          abstract
          tags
          difficulty
          featured
        }
        fields {
          slug
          qualityTier
          readingTime
        }
      }
    }
  }
`;

export default IndexPage;
