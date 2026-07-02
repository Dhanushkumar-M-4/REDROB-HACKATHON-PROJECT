import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Default mock data to show if user navigates to Results directly without running ranker
const mockResults = {
  job_role: "Senior Machine Learning Engineer (Demo)",
  candidates: [
    {
      candidate_id: "CAND-001",
      total_score: 85.0,
      llm_score: 85.0,
      profile: {
        name: "Jane Doe",
        experience_years: 5.0,
        skills: ["Python", "Machine Learning", "TensorFlow", "PyTorch"],
        summary: "Senior ML Engineer with 5 years of experience."
      }
    },
    {
      candidate_id: "CAND-002",
      total_score: 78.5,
      llm_score: 75.0,
      profile: {
        name: "John Smith",
        experience_years: 4.0,
        skills: ["Python", "Data Science", "SQL", "Pandas", "Scikit-Learn"],
        summary: "Data Scientist focusing on predictive modeling."
      }
    },
    {
      candidate_id: "CAND-003",
      total_score: 62.0,
      llm_score: 60.0,
      profile: {
        name: "Alice Johnson",
        experience_years: 2.5,
        skills: ["Java", "Python", "Software Engineering", "Docker"],
        summary: "Software Engineer with basic exposure to Python."
      }
    }
  ]
};

export default function Results({ results }) {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  // Fallback to demo results if no search was run yet
  const activeResults = results || mockResults;
  const candidates = activeResults.candidates || [];

  // Filter candidates based on name or skills
  const filteredCandidates = candidates.filter(cand => {
    const name = (cand.profile?.name || '').toLowerCase();
    const skills = (cand.profile?.skills || []).join(' ').toLowerCase();
    const term = searchTerm.toLowerCase();
    return name.includes(term) || skills.includes(term);
  });

  // Export to CSV helper
  const downloadCSV = () => {
    const headers = ['Rank', 'Candidate ID', 'Name', 'Match Score (LLM)', 'Experience', 'Skills', 'Final Score'];
    const rows = filteredCandidates.map((c, i) => [
      i + 1,
      c.candidate_id,
      c.profile?.name || 'N/A',
      c.llm_score ? c.llm_score.toFixed(1) : '0.0',
      c.profile?.experience_years ? `${c.profile.experience_years} yrs` : 'N/A',
      c.profile?.skills ? c.profile.skills.join(', ') : 'N/A',
      c.total_score ? c.total_score.toFixed(1) : 'N/A'
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))].join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ranked_candidates_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 sm:p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Ranked Candidates</h2>
          <p className="text-gray-500 mt-1">
            Job Role: <span className="font-semibold text-indigo-600">{activeResults.job_role}</span>
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-3">
          <button
            onClick={() => navigate('/rank')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition"
          >
            New Ranking
          </button>
          <button
            onClick={downloadCSV}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition"
          >
            Download CSV
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by name or skills..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full sm:max-w-md border border-gray-300 rounded-md px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
        />
      </div>

      {/* Candidates Table */}
      <div className="overflow-x-auto -mx-6 sm:-mx-8">
        <div className="inline-block min-w-full align-middle px-6 sm:px-8">
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Rank</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Candidate Name</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Match Score</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Experience</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Skills</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Final Score</th>
                  <th scope="col" className="relative px-6 py-3"><span className="sr-only">View Details</span></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCandidates.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="text-center py-8 text-gray-500">
                      No candidates match your search filters.
                    </td>
                  </tr>
                ) : (
                  filteredCandidates.map((cand, index) => {
                    const profile = cand.profile || {};
                    const totalScore = cand.total_score ? cand.total_score.toFixed(1) : 'N/A';
                    const llmScore = cand.llm_score ? cand.llm_score.toFixed(1) : '0.0';
                    const expYears = profile.experience_years ? `${profile.experience_years.toFixed(1)} yrs` : 'N/A';
                    const skills = profile.skills || [];

                    return (
                      <tr key={cand.candidate_id || index} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                          #{index + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{profile.name || 'Unknown'}</div>
                          <div className="text-xs text-gray-400">{cand.candidate_id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                            {llmScore} / 100
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {expYears}
                        </td>
                        <td className="px-6 py-4 max-w-xs truncate text-sm text-gray-500">
                          <div className="flex flex-wrap gap-1">
                            {skills.slice(0, 3).map((s, i) => (
                              <span key={i} className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                                {s}
                              </span>
                            ))}
                            {skills.length > 3 && (
                              <span className="text-xs text-gray-400">+{skills.length - 3} more</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                          {totalScore}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => navigate(`/candidate/${cand.candidate_id}`)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
