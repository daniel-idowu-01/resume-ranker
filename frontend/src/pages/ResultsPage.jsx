import { useState, useEffect } from "react";

const ResultsPage = ({ results, jobDescription, onNewSearch }) => {
  const [sortBy, setSortBy] = useState("score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(false);

  // Sort candidates based on selected criteria
  const sortedCandidates = results?.candidates
    ? [...results.candidates].sort((a, b) => {
        let aValue, bValue;

        switch (sortBy) {
          case "score":
            aValue = a.score;
            bValue = b.score;
            break;
          case "name":
            aValue = a.name.toLowerCase();
            bValue = b.name.toLowerCase();
            break;
          case "experience":
            aValue = a.experience || 0;
            bValue = b.experience || 0;
            break;
          default:
            aValue = a.score;
            bValue = b.score;
        }

        if (sortOrder === "asc") {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      })
    : [];

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 60) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return "Excellent Match";
    if (score >= 60) return "Good Match";
    return "Needs Review";
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return "bg-yellow-500 text-white";
    if (rank === 2) return "bg-gray-400 text-white";
    if (rank === 3) return "bg-amber-600 text-white";
    return "bg-blue-500 text-white";
  };

  const handleDownloadResume = async (candidateId) => {
    setLoading(true);
    try {
      // This would typically make an API call to download the resume
      console.log("Downloading resume for candidate:", candidateId);
      // Implementation would depend on your backend API
    } catch (error) {
      console.error("Error downloading resume:", error);
    } finally {
      setLoading(false);
    }
  };

  const CandidateModal = ({ candidate, onClose }) => {
    if (!candidate) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  {candidate.name}
                </h3>
                <p className="text-gray-600">{candidate.email}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                    candidate.score
                  )}`}
                >
                  {candidate.score}% Match
                </span>
                <span className="text-gray-600">
                  {candidate.experience} years experience
                </span>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Key Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills?.map((skill, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
                <p className="text-gray-700">{candidate.summary}</p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">
                  Match Analysis
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Skills Match:</span>
                    <span className="font-medium">
                      {candidate.skillsMatch || "N/A"}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Experience Match:</span>
                    <span className="font-medium">
                      {candidate.experienceMatch || "N/A"}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Education Match:</span>
                    <span className="font-medium">
                      {candidate.educationMatch || "N/A"}%
                    </span>
                  </div>
                </div>
              </div>

              {candidate.notes && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Notes</h4>
                  <p className="text-gray-700">{candidate.notes}</p>
                </div>
              )}
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => handleDownloadResume(candidate.id)}
                disabled={loading}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? "Downloading..." : "Download Resume"}
              </button>
              <button
                onClick={onClose}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!results || !results.candidates) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No results available
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Upload resumes to see ranking results.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Resume Ranking Results
          </h1>
          <button
            onClick={onNewSearch}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            New Search
          </button>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h2 className="font-semibold text-gray-900 mb-2">
            Job Description Summary
          </h2>
          <p className="text-gray-700 text-sm line-clamp-3">
            {jobDescription?.substring(0, 200)}...
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-blue-600">
            {results.candidates?.length || 0}
          </div>
          <div className="text-sm text-gray-600">Total Candidates</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-green-600">
            {results.candidates?.filter((c) => c.score >= 80).length || 0}
          </div>
          <div className="text-sm text-gray-600">Excellent Matches</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-yellow-600">
            {results.candidates?.filter((c) => c.score >= 60 && c.score < 80)
              .length || 0}
          </div>
          <div className="text-sm text-gray-600">Good Matches</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-gray-600">
            {Math.round(
              results.candidates?.reduce((sum, c) => sum + c.score, 0) /
                results.candidates?.length
            ) || 0}
            %
          </div>
          <div className="text-sm text-gray-600">Average Score</div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm"
          >
            <option value="score">Score</option>
            <option value="name">Name</option>
            <option value="experience">Experience</option>
          </select>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Order:</label>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      {/* Candidates List */}
      <div className="space-y-4">
        {sortedCandidates.map((candidate, index) => (
          <div
            key={candidate.id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div
                  className={`px-3 py-1 rounded-full text-sm font-bold ${getRankBadge(
                    index + 1
                  )}`}
                >
                  #{index + 1}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {candidate.name}
                  </h3>
                  <p className="text-gray-600">{candidate.email}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                      candidate.score
                    )}`}
                  >
                    {candidate.score}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {getScoreLabel(candidate.score)}
                  </div>
                </div>
                <button
                  onClick={() => setSelectedCandidate(candidate)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm"
                >
                  View Details
                </button>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-700">
                  Experience:
                </span>
                <span className="ml-2 text-sm text-gray-600">
                  {candidate.experience} years
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-700">
                  Location:
                </span>
                <span className="ml-2 text-sm text-gray-600">
                  {candidate.location || "Not specified"}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-700">
                  Phone:
                </span>
                <span className="ml-2 text-sm text-gray-600">
                  {candidate.phone || "Not provided"}
                </span>
              </div>
            </div>

            {candidate.skills && (
              <div className="mt-4">
                <span className="text-sm font-medium text-gray-700">
                  Key Skills:
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {candidate.skills.slice(0, 5).map((skill, skillIndex) => (
                    <span
                      key={skillIndex}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                    >
                      {skill}
                    </span>
                  ))}
                  {candidate.skills.length > 5 && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                      +{candidate.skills.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Candidate Detail Modal */}
      <CandidateModal
        candidate={selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
      />
    </div>
  );
};

export default ResultsPage;
