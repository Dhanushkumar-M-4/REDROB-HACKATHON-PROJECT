import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4">
      <div className="max-w-3xl">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight mb-6">
          AI Candidate Ranking System
        </h1>
        <p className="text-lg sm:text-xl text-gray-500 mb-8 leading-relaxed">
          Streamline your recruitment process with semantic candidate search and deep LLM evaluations. 
          Upload your job requirements and instantly find the most qualified candidates in your dataset.
        </p>
        <button
          onClick={() => navigate('/rank')}
          className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-semibold rounded-md text-white bg-indigo-600 hover:bg-indigo-700 shadow-md transition duration-150 ease-in-out"
        >
          Start Ranking
        </button>
      </div>
    </div>
  );
}
