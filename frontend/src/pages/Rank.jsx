import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rankingService } from '../services/api';

export default function Rank({ setResults }) {
  const navigate = useNavigate();
  const [jdText, setJdText] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [candidateFile, setCandidateFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState('llama3');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jdText.trim() && !jdFile) {
      setError('Please provide a Job Description (paste text or upload a file).');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    if (jdFile) {
      formData.append('file', jdFile);
    } else {
      formData.append('job_description', jdText);
    }

    if (candidateFile) {
      formData.append('candidates_file', candidateFile);
    }
    
    // We send selected model as well (if backend supports it, otherwise it fallback to config default)
    formData.append('model', selectedModel);

    try {
      const data = await rankingService.rankCandidates(formData);
      setResults(data);
      navigate('/results');
    } catch (err) {
      setError(err.message || 'An error occurred during evaluation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white shadow-sm border border-gray-200 rounded-lg p-6 sm:p-8">
      <h2 className="text-3xl font-bold text-gray-900 mb-2">Rank Candidates</h2>
      <p className="text-gray-500 mb-8">
        Configure the ranking system by providing the Job Description and candidate files.
      </p>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 rounded">
          <div className="flex">
            <div className="flex-shrink-0">⚠️</div>
            <div className="ml-3">
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <h3 className="text-lg font-semibold text-gray-900">Processing Candidates...</h3>
          <p className="text-sm text-gray-500 mt-2 text-center max-w-md">
            This will take a moment as our AI model conducts semantic search and evaluates candidate profiles.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Description Textarea */}
          <div className="flex flex-col">
            <label htmlFor="jd-text" className="text-sm font-semibold text-gray-700 mb-2">
              Job Description (Paste Text)
            </label>
            <textarea
              id="jd-text"
              rows={6}
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value);
                if (e.target.value.trim()) setJdFile(null); // Clear file if text is typed
              }}
              placeholder="Paste the job description or requirements here..."
              className="border border-gray-300 rounded-md p-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            />
          </div>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-gray-200"></div>
            <span className="flex-shrink mx-4 text-gray-400 text-xs font-semibold uppercase tracking-wider">OR</span>
            <div className="flex-grow border-t border-gray-200"></div>
          </div>

          {/* Job Description File Upload */}
          <div className="flex flex-col">
            <label htmlFor="jd-file" className="text-sm font-semibold text-gray-700 mb-2">
              Upload Job Description File (TXT/PDF)
            </label>
            <input
              id="jd-file"
              type="file"
              accept=".txt,.pdf"
              onChange={(e) => {
                const file = e.target.files[0];
                setJdFile(file);
                if (file) setJdText(''); // Clear text if file is uploaded
              }}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition"
            />
            {jdFile && <p className="text-xs text-indigo-600 mt-1">Selected: {jdFile.name}</p>}
          </div>

          <div className="border-t border-gray-100 pt-6"></div>

          {/* Candidate Dataset File Upload */}
          <div className="flex flex-col">
            <label htmlFor="candidate-file" className="text-sm font-semibold text-gray-700 mb-2">
              Candidate Dataset (CSV/JSON)
            </label>
            <input
              id="candidate-file"
              type="file"
              accept=".csv,.json"
              onChange={(e) => setCandidateFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition"
            />
            <p className="text-xs text-gray-400 mt-1">
              Optional: Overwrite default candidate dataset. Leaving blank uses candidates currently loaded in backend.
            </p>
            {candidateFile && <p className="text-xs text-indigo-600 mt-1">Selected: {candidateFile.name}</p>}
          </div>

          {/* Dropdown for LLM Selection */}
          <div className="flex flex-col">
            <label htmlFor="llm-model" className="text-sm font-semibold text-gray-700 mb-2">
              Select LLM Model
            </label>
            <select
              id="llm-model"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="border border-gray-300 rounded-md p-3 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            >
              <option value="llama3">Llama 3 (Recommended)</option>
              <option value="llama3.2">Llama 3.2 (Faster)</option>
              <option value="qwen2.5">Qwen 2.5</option>
              <option value="mistral">Mistral</option>
            </select>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-semibold rounded-md text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition duration-150 ease-in-out"
          >
            Rank Candidates
          </button>
        </form>
      )}
    </div>
  );
}
