import React from "react";
import { graphql, PageProps, Link } from "gatsby";
import Layout from "../components/Layout";

interface DiscoveryNode {
  id: string;
  frontmatter: {
    title: string;
    date: string;
    source: string;
    arxivId?: string;
    similarityScore: number;
    excerpt: string;
    tags: string[];
  };
  fields: { slug: string };
}

const IndexPage: React.FC<PageProps<{ allMdx: { nodes: DiscoveryNode[] } }>> = ({ data }) => {
  const discoveries = data?.allMdx?.nodes || [];

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl lg:text-5xl font-bold mb-6 font-heading">
            AI Research Discovery
          </h1>
          <p className="text-xl lg:text-2xl text-blue-100 max-w-3xl mx-auto">
            Daily curated analysis of cutting-edge ML/AI papers.
            Powered by <strong className="text-white">Swarm-It</strong> multi-agent certification.
          </p>
        </div>
      </section>

      {/* Discoveries Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl lg:text-3xl font-bold text-gray-900">Latest Reviews</h2>
            <span className="text-gray-600 bg-gray-200 px-4 py-2 rounded-full text-sm font-medium">
              {discoveries.length} papers reviewed
            </span>
          </div>

          {discoveries.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="max-w-md mx-auto">
                <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-600 text-lg mb-2">No discoveries yet.</p>
                <p className="text-gray-500">The scanner runs daily, matching papers against representation learning, multi-agent systems, and AI safety topics.</p>
              </div>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {discoveries.map((node) => (
                <article
                  key={node.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
                    <span>{node.frontmatter.date}</span>
                    <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                    <span>{node.frontmatter.source}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 line-clamp-2">
                    <Link
                      to={node.fields.slug}
                      className="hover:text-blue-600 transition-colors"
                    >
                      {node.frontmatter.title}
                    </Link>
                  </h3>
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {node.frontmatter.excerpt}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        node.frontmatter.similarityScore >= 0.8
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {Math.round(node.frontmatter.similarityScore * 100)}% match
                    </span>
                    {node.frontmatter.tags.slice(0, 2).map(t => (
                      <span key={t} className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                        {t}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 text-center mb-12">How It Works</h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {[
              { step: "1", title: "Daily Scan", desc: "Monitor arXiv & archives" },
              { step: "2", title: "Match", desc: "Semantic similarity to topics" },
              { step: "3", title: "Certify", desc: "3-agent RSCT analysis" },
              { step: "4", title: "Publish", desc: "Auto-generate reviews" },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  );
};

export const query = graphql`
  query {
    allMdx(sort: {frontmatter: {date: DESC}}, limit: 20) {
      nodes {
        id
        frontmatter { title, date(formatString: "MMM DD, YYYY"), source, arxivId, similarityScore, excerpt, tags }
        fields { slug }
      }
    }
  }
`;

export default IndexPage;
