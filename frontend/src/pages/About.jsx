import React from 'react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-sm p-6 sm:p-8 space-y-8">
      {/* Objective */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">About the System</h2>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Project Objective</h3>
        <p className="text-gray-500 leading-relaxed text-sm">
          The AI Candidate Ranking System is designed to automate and augment the initial recruitment pre-screening stage.
          By combining semantic search and Large Language Models, the system evaluates how well candidate CVs match 
          complicated job requirements, producing a ranked shortlist of top talent. This reduces recruiter bias, speeds 
          up time-to-hire, and ensures high-quality talent matches.
        </p>
      </div>

      <hr className="border-gray-200" />

      {/* Technologies Used */}
      <div>
        <h3 className="text-lg font-semibold text-gray-700 mb-3">Technologies Used</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="border border-gray-100 rounded p-4 bg-gray-50">
            <h4 className="font-semibold text-gray-900 text-sm mb-1">Backend & AI Pipeline</h4>
            <ul className="list-disc pl-4 text-xs text-gray-500 space-y-1">
              <li>Python & FastAPI</li>
              <li>Sentence Transformers (`all-MiniLM-L6-v2`)</li>
              <li>FAISS (Vector Database)</li>
              <li>Ollama (Local LLM Llama3 execution)</li>
            </ul>
          </div>
          <div className="border border-gray-100 rounded p-4 bg-gray-50">
            <h4 className="font-semibold text-gray-900 text-sm mb-1">Frontend Client</h4>
            <ul className="list-disc pl-4 text-xs text-gray-500 space-y-1">
              <li>React + Vite</li>
              <li>Tailwind CSS</li>
              <li>Axios</li>
              <li>React Router</li>
            </ul>
          </div>
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* How it Works */}
      <div>
        <h3 className="text-lg font-semibold text-gray-700 mb-3">How the Ranking System Works</h3>
        <ol className="space-y-4 text-sm text-gray-500">
          <li className="flex gap-4">
            <span className="flex-shrink-0 flex items-center justify-center font-bold text-xs h-6 w-6 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700">1</span>
            <div>
              <strong className="text-gray-900">Job Description Parsing:</strong> The system takes a text input or uploaded document, extracting the primary requirements (such as skills, years of experience, and responsibilities).
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex-shrink-0 flex items-center justify-center font-bold text-xs h-6 w-6 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700">2</span>
            <div>
              <strong className="text-gray-900">Semantic Search (FAISS Retrieval):</strong> Candidates are parsed, converted into high-dimensional vector embeddings, and indexed. The Job Description query is matched against the FAISS index to instantly pull the most semantically relevant profiles.
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex-shrink-0 flex items-center justify-center font-bold text-xs h-6 w-6 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700">3</span>
            <div>
              <strong className="text-gray-900">LLM Deep Evaluation:</strong> The top matching candidate profiles are sent to a local Large Language Model (e.g., Llama 3 via Ollama) which parses their background and grades them on specific traits (technical skills, work experience, projects) while producing reasoning feedback.
            </div>
          </li>
          <li className="flex gap-4">
            <span className="flex-shrink-0 flex items-center justify-center font-bold text-xs h-6 w-6 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700">4</span>
            <div>
              <strong className="text-gray-900">Hybrid Scoring & Sorting:</strong> The semantic score, LLM score, experience years, and skill flags are calculated together using custom weights. Candidates are then sorted by this hybrid score and presented in the results dashboard.
            </div>
          </li>
        </ol>
      </div>
    </div>
  );
}
