import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Rank from './pages/Rank';
import Results from './pages/Results';
import CandidateDetails from './pages/CandidateDetails';
import About from './pages/About';

export default function App() {
  // Shared state to hold the latest ranking results
  const [results, setResults] = useState(null);

  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Navbar />
        <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/rank" element={<Rank setResults={setResults} />} />
            <Route path="/results" element={<Results results={results} />} />
            <Route path="/candidate/:id" element={<CandidateDetails />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
