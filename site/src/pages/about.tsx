import React from "react";
import Layout from "../components/Layout";
import { Link } from "gatsby";

const AboutPage: React.FC = () => {
  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 dark:from-blue-800 dark:via-purple-800 dark:to-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl lg:text-5xl font-bold mb-4 font-heading">
            About Swarm-It Discovery
          </h1>
          <p className="text-xl text-blue-100 dark:text-blue-200 max-w-3xl">
            Automated research paper discovery powered by RSCT certification and κ-gate quality scoring.
          </p>
        </div>
      </section>

      {/* What We Do Section */}
      <section className="py-16 bg-white dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">What We Do</h2>

          <div className="prose prose-lg dark:prose-invert max-w-none">
            <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed mb-6">
              Swarm-It Discovery automatically scans arXiv and other sources for new research papers, matches them against curated topics, and certifies their quality using <strong>RSCT (Representation Solver Compatibility Testing)</strong>.
            </p>

            <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed">
              Unlike traditional paper aggregators that rely on keywords or citations, we use <strong>semantic similarity</strong> and <strong>multi-agent certification</strong> to find papers that are genuinely relevant to cutting-edge AI research topics.
            </p>
          </div>
        </div>
      </section>

      {/* RSCT Methodology Section */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">RSCT Certification</h2>

          <div className="space-y-8">
            {/* RSN Decomposition */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">RSN Decomposition</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Every paper is decomposed into three components that sum to 1.0 (simplex constraint):
              </p>

              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center text-2xl mr-4">
                    📊
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-gray-100 mb-1">Relevance (R)</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      The portion of the paper that directly addresses research goals and topics.
                      High R means the paper is on-target.
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-2xl mr-4">
                    🔗
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-gray-100 mb-1">Spurious (S)</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      Supporting context, correlations, and related concepts that aren't directly relevant but provide useful background.
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center text-2xl mr-4">
                    🔇
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-gray-100 mb-1">Noise (N)</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      Irrelevant information, boilerplate, or content unrelated to the research focus.
                      Low N is better.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  <strong>Simplex Constraint:</strong> R + S + N = 1.0 (always)
                </p>
              </div>
            </div>

            {/* Kappa Gate */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">κ-gate Quality Scoring</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                The <strong>kappa (κ) score</strong> represents overall quality and compatibility.
                It's a single number (0-1) that summarizes how well the paper passes our quality gates.
              </p>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                  <div className="flex items-center">
                    <span className="text-3xl mr-3">🥇</span>
                    <div>
                      <div className="font-bold text-gray-900 dark:text-gray-100">Exceptional</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Gold tier certification</div>
                    </div>
                  </div>
                  <div className="text-xl font-bold text-amber-600 dark:text-amber-400">κ ≥ 0.9</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="flex items-center">
                    <span className="text-3xl mr-3">🥈</span>
                    <div>
                      <div className="font-bold text-gray-900 dark:text-gray-100">High Quality</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Silver tier certification</div>
                    </div>
                  </div>
                  <div className="text-xl font-bold text-gray-600 dark:text-gray-300">κ ≥ 0.8</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                  <div className="flex items-center">
                    <span className="text-3xl mr-3">🥉</span>
                    <div>
                      <div className="font-bold text-gray-900 dark:text-gray-100">Certified</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Bronze tier certification</div>
                    </div>
                  </div>
                  <div className="text-xl font-bold text-orange-600 dark:text-orange-400">κ ≥ 0.7</div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                <p className="text-sm text-purple-900 dark:text-purple-100">
                  <strong>Quality Threshold:</strong> Only papers with κ ≥ 0.7 are published. This ensures all reviews meet a minimum quality standard.
                </p>
              </div>
            </div>

            {/* Multi-Agent Swarm */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">Multi-Agent Certification</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                RSCT certification uses a <strong>swarm of specialized agents</strong> to evaluate each paper from multiple perspectives:
              </p>

              <div className="grid md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="text-2xl mb-2">🔍</div>
                  <div className="font-bold text-gray-900 dark:text-gray-100 mb-1">Scanner Agent</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Fetches and validates input</p>
                </div>

                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                  <div className="text-2xl mb-2">🧠</div>
                  <div className="font-bold text-gray-900 dark:text-gray-100 mb-1">Analyzer Agent</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Matches against topics</p>
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="text-2xl mb-2">📝</div>
                  <div className="font-bold text-gray-900 dark:text-gray-100 mb-1">Publisher Agent</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Generates reviews</p>
                </div>
              </div>

              <p className="text-gray-600 dark:text-gray-400 mt-6">
                Each agent certifies its output before passing to the next stage.
                This creates a <strong>certified pipeline</strong> where quality is validated at every step.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pipeline Section */}
      <section className="py-16 bg-white dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">The Pipeline</h2>

          <div className="space-y-6">
            {[
              {
                step: "1",
                title: "Daily Scan",
                desc: "Automatically fetch new papers from arXiv, bioRxiv, and other sources. The scanner agent validates inputs and checks for duplicates.",
                icon: "🔍"
              },
              {
                step: "2",
                title: "Semantic Matching",
                desc: "Convert paper abstracts to embeddings and compute cosine similarity against curated research topics. Papers above the threshold (typically 0.5+) proceed to certification.",
                icon: "🎯"
              },
              {
                step: "3",
                title: "RSCT Certification",
                desc: "Multi-agent swarm analyzes each paper, computing R/S/N decomposition and κ-gate scores. Only papers with κ ≥ 0.7 are published.",
                icon: "✅"
              },
              {
                step: "4",
                title: "Review Generation",
                desc: "LLM-powered analysis generates comprehensive reviews with key insights, technical contributions, and relevance to AI safety and multi-agent systems.",
                icon: "📄"
              },
              {
                step: "5",
                title: "Publication",
                desc: "Reviews are published to this site with full RSCT metrics, tags, and difficulty ratings. Users can search, filter, and explore by topic.",
                icon: "🚀"
              }
            ].map((item) => (
              <div key={item.step} className="flex items-start p-6 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
                <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 dark:from-blue-600 dark:to-purple-700 rounded-2xl flex items-center justify-center text-white text-3xl font-bold mr-6">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <span className="mr-2">{item.icon}</span>
                    {item.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-16 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">Technology Stack</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Frontend</h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• <strong>Gatsby 5</strong> - Static site generation</li>
                <li>• <strong>React 18</strong> - UI components</li>
                <li>• <strong>TypeScript</strong> - Type safety</li>
                <li>• <strong>Tailwind CSS</strong> - Styling with dark mode</li>
                <li>• <strong>GraphQL</strong> - Data layer</li>
              </ul>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Backend Pipeline</h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• <strong>Python 3.11+</strong> - Pipeline orchestration</li>
                <li>• <strong>OpenAI API</strong> - Embeddings & analysis</li>
                <li>• <strong>Swarm-It Sidecar</strong> - RSCT certification</li>
                <li>• <strong>arXiv API</strong> - Paper discovery</li>
                <li>• <strong>AWS Lambda</strong> - Scheduled execution</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <p className="text-gray-700 dark:text-gray-300">
              <strong>Patent Notice:</strong> The RSCT methodology and κ-gate scoring system are patent-pending technology developed by Next Shift Consulting.
              See <a href="https://nextshiftconsulting.com/patents" className="text-blue-600 dark:text-blue-400 hover:underline">patent documentation</a> for details.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-br from-blue-600 to-purple-600 dark:from-blue-800 dark:to-purple-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4">Start Exploring</h2>
          <p className="text-xl text-blue-100 dark:text-blue-200 mb-8">
            Browse RSCT-certified papers or explore research topics.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/reviews"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-bold hover:bg-blue-50 transition-colors shadow-lg"
            >
              View All Papers
            </Link>
            <Link
              to="/topics"
              className="px-8 py-3 bg-blue-700 hover:bg-blue-800 text-white rounded-lg font-bold transition-colors shadow-lg border-2 border-blue-400"
            >
              Explore Topics
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
};

export default AboutPage;
