import React, { useState } from "react";
import { graphql, PageProps, Link } from "gatsby";
import Layout from "../components/Layout";
import { SearchBox } from "../components/search/SearchBox";

interface ReviewNode {
  id: string;
  frontmatter: {
    title: string;
    published_date: string;
    published_date_raw: string;
    arxiv_id: string;
    kappa: number;
    R: number;
    S: number;
    N: number;
    abstract: string;
    tags: string[];
    primary_topic: string;
    difficulty: string;
    featured?: boolean;
  };
  fields: {
    slug: string;
    qualityTier: string;
    readingTime: number;
  };
}

const ReviewsPage: React.FC<PageProps<{ allMdx: { nodes: ReviewNode[] } }>> = ({ data }) => {
  const allReviews = data?.allMdx?.nodes || [];
  const [filterTopic, setFilterTopic] = useState<string>("all");
  const [filterQuality, setFilterQuality] = useState<string>("all");
  const [filterExpertise, setFilterExpertise] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"date" | "quality">("date");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Check if any filters are active
  const hasActiveFilters = filterTopic !== "all" || filterQuality !== "all" || filterExpertise !== "all" || searchQuery !== "";

  // Clear all filters
  const handleClearFilters = () => {
    setFilterTopic("all");
    setFilterQuality("all");
    setFilterExpertise("all");
    setSearchQuery("");
  };

  // Extract unique topics
  const allTopics = Array.from(new Set(allReviews.map(r => r.frontmatter.primary_topic))).sort();

  // Filter reviews
  const filteredReviews = allReviews.filter(review => {
    const topicMatch = filterTopic === "all" || review.frontmatter.primary_topic === filterTopic;
    const qualityMatch =
      filterQuality === "all" ||
      (filterQuality === "exceptional" && review.frontmatter.kappa >= 0.9) ||
      (filterQuality === "high-quality" && review.frontmatter.kappa >= 0.8 && review.frontmatter.kappa < 0.9) ||
      (filterQuality === "certified" && review.frontmatter.kappa >= 0.7 && review.frontmatter.kappa < 0.8);
    const expertiseMatch = filterExpertise === "all" || review.frontmatter.difficulty === filterExpertise;
    const searchMatch = searchQuery === "" ||
      review.frontmatter.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      review.frontmatter.abstract.toLowerCase().includes(searchQuery.toLowerCase()) ||
      review.frontmatter.primary_topic.toLowerCase().includes(searchQuery.toLowerCase());
    return topicMatch && qualityMatch && expertiseMatch && searchMatch;
  });

  // Sort reviews
  const sortedReviews = [...filteredReviews].sort((a, b) => {
    if (sortBy === "date") {
      return new Date(b.frontmatter.published_date_raw).getTime() -
             new Date(a.frontmatter.published_date_raw).getTime();
    }
    return b.frontmatter.kappa - a.frontmatter.kappa;
  });

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
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 dark:from-blue-800 dark:via-purple-800 dark:to-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl lg:text-5xl font-bold mb-4 font-heading">
            Paper Reviews
          </h1>
          <p className="text-xl text-blue-100 dark:text-blue-200 max-w-3xl mb-8">
            All RSCT-certified research papers, ranked by κ-gate quality scores.
          </p>

          {/* Search Box */}
          <div className="max-w-2xl">
            <SearchBox
              placeholder="Search by title, abstract, or topic..."
              className="w-full"
              onSearch={setSearchQuery}
            />
          </div>
        </div>
      </section>

      {/* Filters Section */}
      <section className="py-8 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap gap-4 items-end">
            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sort by
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as "date" | "quality")}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">Date (Newest)</option>
                <option value="quality">Quality (Highest)</option>
              </select>
            </div>

            {/* Topic Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Topic
              </label>
              <select
                value={filterTopic}
                onChange={(e) => setFilterTopic(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Topics</option>
                {allTopics.map(topic => (
                  <option key={topic} value={topic}>{topic}</option>
                ))}
              </select>
            </div>

            {/* Quality Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Quality
              </label>
              <select
                value={filterQuality}
                onChange={(e) => setFilterQuality(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Quality Tiers</option>
                <option value="exceptional">🥇 Exceptional (κ ≥ 0.9)</option>
                <option value="high-quality">🥈 High Quality (κ ≥ 0.8)</option>
                <option value="certified">🥉 Certified (κ ≥ 0.7)</option>
              </select>
            </div>

            {/* Expertise Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Expertise
              </label>
              <select
                value={filterExpertise}
                onChange={(e) => setFilterExpertise(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Levels</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
              >
                Clear Filters ✕
              </button>
            )}

            {/* Results Count */}
            <div className="ml-auto">
              <span className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300">
                {sortedReviews.length} paper{sortedReviews.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Reviews Grid */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {sortedReviews.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
              <p className="text-gray-600 dark:text-gray-300 text-lg">No papers match your filters.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {sortedReviews.map((node) => (
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

                  {/* RSCT Metrics */}
                  <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">RSN Decomposition</div>
                    <div className="flex justify-between text-xs">
                      <span className="text-green-600 dark:text-green-400">R: {node.frontmatter.R.toFixed(2)}</span>
                      <span className="text-blue-600 dark:text-blue-400">S: {node.frontmatter.S.toFixed(2)}</span>
                      <span className="text-gray-600 dark:text-gray-400">N: {node.frontmatter.N.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {getQualityTierBadge(node.fields.qualityTier, node.frontmatter.kappa)}

                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200">
                      {node.frontmatter.primary_topic}
                    </span>
                  </div>

                  {/* arXiv Link */}
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
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
    </Layout>
  );
};

export const query = graphql`
  query {
    allMdx(
      filter: {frontmatter: {status: {eq: "live"}}}
    ) {
      nodes {
        id
        frontmatter {
          title
          published_date(formatString: "MMM DD, YYYY")
          published_date_raw: published_date
          arxiv_id
          kappa
          R
          S
          N
          abstract
          tags
          primary_topic
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

export default ReviewsPage;
