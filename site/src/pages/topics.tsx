import React from "react";
import { graphql, PageProps, Link } from "gatsby";
import Layout from "../components/Layout";

interface TopicData {
  id: string;
  title: string;
  content: string;
  keywords: string[];
}

interface ReviewNode {
  frontmatter: {
    primary_topic: string;
    kappa: number;
  };
}

const TopicsPage: React.FC<PageProps<{ allMdx: { nodes: ReviewNode[] }; topicsJson: { topics: TopicData[] } }>> = ({ data }) => {
  const topics = data?.topicsJson?.topics || [];
  const reviews = data?.allMdx?.nodes || [];

  // Count papers per topic
  const topicCounts: Record<string, number> = {};
  const topicAvgKappa: Record<string, number[]> = {};

  reviews.forEach(review => {
    const topic = review.frontmatter.primary_topic;
    topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    topicAvgKappa[topic] = [...(topicAvgKappa[topic] || []), review.frontmatter.kappa];
  });

  const getTopicIcon = (id: string) => {
    const icons: Record<string, string> = {
      'rsct-core': '🎯',
      'ai-safety': '🛡️',
      'representation-learning': '🧠',
      'multi-agent': '🤝',
      'llm-agents': '🤖'
    };
    return icons[id] || '📚';
  };

  const getAvgKappa = (topicTitle: string): number => {
    const kappas = topicAvgKappa[topicTitle] || [];
    if (kappas.length === 0) return 0;
    return kappas.reduce((sum, k) => sum + k, 0) / kappas.length;
  };

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 dark:from-blue-800 dark:via-purple-800 dark:to-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl lg:text-5xl font-bold mb-4 font-heading">
            Research Topics
          </h1>
          <p className="text-xl text-blue-100 dark:text-blue-200 max-w-3xl">
            Key research areas we track. Papers are matched using semantic similarity to these topic definitions.
          </p>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">{topics.length}</div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">Active Topics</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">{reviews.length}</div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">Papers Indexed</div>
            </div>
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-6 border border-amber-200 dark:border-amber-800">
              <div className="text-3xl font-bold text-amber-600 dark:text-amber-400 mb-1">
                {reviews.filter(r => r.frontmatter.kappa >= 0.7).length}
              </div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">κ-gate Certified</div>
            </div>
          </div>
        </div>
      </section>

      {/* Topics Grid */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-2">
            {topics.map((topic) => {
              const paperCount = topicCounts[topic.title] || 0;
              const avgKappa = getAvgKappa(topic.title);

              return (
                <article
                  key={topic.id}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 hover:shadow-md transition-shadow"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="text-4xl mb-2">{getTopicIcon(topic.id)}</div>
                      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {topic.title}
                      </h2>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{paperCount}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">papers</div>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
                    {topic.content.split(' ').slice(0, 25).join(' ')}...
                  </p>

                  {/* Keywords */}
                  <div className="mb-6">
                    <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                      Key Concepts
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {topic.keywords.map(keyword => (
                        <span
                          key={keyword}
                          className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-xs font-medium"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Stats */}
                  {paperCount > 0 && (
                    <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">Avg κ-score</div>
                          <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                            {avgKappa.toFixed(3)}
                          </div>
                        </div>
                        <Link
                          to={`/reviews?topic=${encodeURIComponent(topic.title)}`}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          View Papers →
                        </Link>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* How Topics Work Section */}
      <section className="py-16 bg-white dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
            How Topic Matching Works
          </h2>
          <div className="prose prose-lg dark:prose-invert max-w-none">
            <p className="text-gray-600 dark:text-gray-400">
              Each topic is defined by a set of keywords and concepts. When a new paper is discovered:
            </p>
            <ol className="text-gray-600 dark:text-gray-400 space-y-2">
              <li><strong>Semantic Embedding:</strong> The paper's title and abstract are converted to vector embeddings</li>
              <li><strong>Similarity Matching:</strong> Cosine similarity is computed against each topic's embedding</li>
              <li><strong>Threshold Filter:</strong> Papers above the similarity threshold (typically 0.5+) are matched</li>
              <li><strong>RSCT Certification:</strong> Matched papers are certified using κ-gate quality scoring</li>
            </ol>
            <p className="text-gray-600 dark:text-gray-400 mt-4">
              This approach ensures we capture papers that are semantically relevant, even if they don't use exact keyword matches.
            </p>
          </div>
        </div>
      </section>
    </Layout>
  );
};

export const query = graphql`
  query {
    allMdx(filter: {frontmatter: {status: {eq: "live"}}}) {
      nodes {
        frontmatter {
          primary_topic
          kappa
        }
      }
    }
    topicsJson {
      topics {
        id
        title
        content
        keywords
      }
    }
  }
`;

export default TopicsPage;
