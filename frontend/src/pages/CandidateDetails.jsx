import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { rankingService } from '../services/api';

export default function CandidateDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const data = await rankingService.getCandidateById(id);
        setCandidate(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch candidate details');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-gray-500">Loading profile details...</p>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="max-w-3xl mx-auto bg-white border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Candidate</h3>
        <p className="text-gray-500 mb-6">{error || 'Candidate details could not be found.'}</p>
        <button
          onClick={() => navigate('/results')}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition"
        >
          Back to Results
        </button>
      </div>
    );
  }

  const profile = candidate.profile || {};
  const llm = candidate.llm_evaluation || {};
  const totalScore = candidate.total_score ? candidate.total_score.toFixed(1) : 'N/A';
  const llmScore = candidate.llm_score ? candidate.llm_score.toFixed(1) : 'N/A';

  return (
    <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-6 sm:px-8 bg-gray-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/results')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 uppercase tracking-wider mb-2 block"
          >
            ← Back to Results
          </button>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">{profile.name || 'Unknown Candidate'}</h2>
          <p className="text-xs text-gray-400 mt-1">ID: {candidate.candidate_id}</p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-right">
            <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">AI Match Score</span>
            <span className="text-3xl font-extrabold text-indigo-600 font-mono">{llmScore}</span>
          </div>
          <div className="h-8 border-l border-gray-300"></div>
          <div className="text-right">
            <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">Final Score</span>
            <span className="text-3xl font-extrabold text-green-600 font-mono">{totalScore}</span>
          </div>
        </div>
      </div>

      <div className="p-6 sm:p-8 space-y-8">
        {/* Recommendation Reason */}
        {llm.reasoning && (
          <div className="bg-indigo-50 border-l-4 border-indigo-500 p-6 rounded-r-md">
            <h4 className="text-sm font-semibold text-indigo-950 uppercase tracking-wider mb-2">
              AI Recommendation Reason
            </h4>
            <p className="text-indigo-900 text-sm leading-relaxed whitespace-pre-wrap">{llm.reasoning}</p>
          </div>
        )}

        {/* Detailed Scores Breakdown */}
        {llm.technical_skill_match !== undefined && (
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">AI Score Breakdown</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center">
                <span className="text-xs text-gray-400 font-semibold uppercase block mb-1">Technical Skills</span>
                <span className="text-xl font-bold text-gray-900 font-mono">{llm.technical_skill_match}/10</span>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center">
                <span className="text-xs text-gray-400 font-semibold uppercase block mb-1">Relevant Experience</span>
                <span className="text-xl font-bold text-gray-900 font-mono">{llm.relevant_experience}/10</span>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center">
                <span className="text-xs text-gray-400 font-semibold uppercase block mb-1">Projects Relevance</span>
                <span className="text-xl font-bold text-gray-900 font-mono">{llm.project_relevance}/10</span>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded p-4 text-center">
                <span className="text-xs text-gray-400 font-semibold uppercase block mb-1">Overall Fit</span>
                <span className="text-xl font-bold text-gray-900 font-mono">{llm.overall_fit}/10</span>
              </div>
            </div>
          </div>
        )}

        {/* Experience & Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Work Experience</h3>
            <p className="text-lg font-bold text-gray-900">
              {profile.experience_years ? `${profile.experience_years.toFixed(1)} Years` : 'N/A'}
            </p>
          </div>
          <div className="md:col-span-2">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Candidate Summary</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{profile.summary || 'No summary listed.'}</p>
          </div>
        </div>

        {/* Skills */}
        <div>
          <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-100 pb-2">Skills</h3>
          <div className="flex flex-wrap gap-2">
            {profile.skills && profile.skills.length > 0 ? (
              profile.skills.map((skill, i) => (
                <span key={i} className="px-3 py-1 bg-gray-100 border border-gray-200 text-gray-700 text-sm font-medium rounded-full">
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-gray-400 text-sm">No skills specified</span>
            )}
          </div>
        </div>

        {/* Projects & Education */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-100 pb-2">Education</h3>
            <p className="text-gray-700 text-sm">{profile.education || 'Not specified'}</p>
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-100 pb-2">Notable Projects</h3>
            {profile.projects && profile.projects.length > 0 ? (
              <ul className="list-disc pl-5 text-gray-700 text-sm space-y-2">
                {profile.projects.map((proj, i) => (
                  <li key={i}>{proj}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 text-sm">None listed</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
