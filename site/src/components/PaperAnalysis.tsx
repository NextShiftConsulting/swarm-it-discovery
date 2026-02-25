import React from "react";

interface PaperAnalysisProps {
  score: number;
  topics: string[];
  source: string;
}

export const PaperAnalysis: React.FC<PaperAnalysisProps> = ({ score, topics, source }) => {
  const scorePercent = Math.round(score * 100);
  const scoreClass = score >= 0.8 ? "high" : score >= 0.6 ? "medium" : "low";

  return (
    <div className="paper-analysis">
      <h4>Swarm-It Analysis</h4>
      <div className="metrics">
        <div className="metric">
          <div className={`metric-value ${scoreClass}`}>{scorePercent}%</div>
          <div className="metric-label">Relevance Score</div>
        </div>
        <div className="metric">
          <div className="metric-value">{topics.length}</div>
          <div className="metric-label">Topics Matched</div>
        </div>
        <div className="metric">
          <div className="metric-value">{source}</div>
          <div className="metric-label">Source</div>
        </div>
      </div>
      {topics.length > 0 && (
        <div className="matched-topics">
          <strong>Matched Topics:</strong> {topics.join(", ")}
        </div>
      )}
    </div>
  );
};

export default PaperAnalysis;
