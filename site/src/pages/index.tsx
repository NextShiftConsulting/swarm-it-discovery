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
      <section className="hero">
        <h1>AI Research Discovery</h1>
        <p className="hero-subtitle">
          Daily curated analysis of cutting-edge ML/AI papers.
          Powered by <strong>Swarm-It</strong> multi-agent certification.
        </p>
      </section>

      <section className="discoveries">
        <div className="section-header">
          <h2>Latest Discoveries</h2>
          <span className="discovery-count">{discoveries.length} papers</span>
        </div>

        {discoveries.length === 0 ? (
          <div className="empty-state">
            <p>No discoveries yet. The scanner runs daily.</p>
            <p className="hint">Papers matched against representation learning, multi-agent systems, AI safety.</p>
          </div>
        ) : (
          <div className="discoveries-grid">
            {discoveries.map((node) => (
              <article key={node.id} className="discovery-card">
                <div className="meta">
                  <span>{node.frontmatter.date}</span>
                  <span>{node.frontmatter.source}</span>
                </div>
                <h3><Link to={node.fields.slug}>{node.frontmatter.title}</Link></h3>
                <p className="excerpt">{node.frontmatter.excerpt}</p>
                <div className="tags">
                  <span className={`tag relevance-${node.frontmatter.similarityScore >= 0.8 ? 'high' : 'medium'}`}>
                    {Math.round(node.frontmatter.similarityScore * 100)}% match
                  </span>
                  {node.frontmatter.tags.slice(0, 2).map(t => <span key={t} className="tag">{t}</span>)}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="about-methodology">
        <h2>How It Works</h2>
        <div className="methodology-grid">
          <div className="method-card"><div className="method-icon">1</div><h3>Daily Scan</h3><p>Monitor arXiv & archives</p></div>
          <div className="method-card"><div className="method-icon">2</div><h3>Match</h3><p>Semantic similarity to topics</p></div>
          <div className="method-card"><div className="method-icon">3</div><h3>Certify</h3><p>3-agent RSCT analysis</p></div>
          <div className="method-card"><div className="method-icon">4</div><h3>Publish</h3><p>Auto-generate blog posts</p></div>
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
