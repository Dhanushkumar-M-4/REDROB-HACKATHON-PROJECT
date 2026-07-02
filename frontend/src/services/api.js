import axios from 'axios';

// Create Axios instance with default settings
const api = axios.create({
  // Use relative path so Vite proxy routes to backend in development
  baseURL: '',
  timeout: 180000, // 3 minutes because LLM ranking takes time
});

// Sample Mock Data in case backend is unavailable
const mockCandidates = [
  {
    candidate_id: "CAND-001",
    total_score: 85.0,
    llm_score: 85.0,
    profile: {
      name: "Jane Doe",
      experience_years: 5.0,
      skills: ["Python", "Machine Learning", "TensorFlow", "PyTorch"],
      projects: ["Built recommendation engine serving 1M users"],
      education: "M.S. Computer Science, Stanford University",
      summary: "Senior ML Engineer with 5 years of experience."
    },
    llm_evaluation: {
      technical_skill_match: 9.0,
      relevant_experience: 8.0,
      project_relevance: 9.0,
      overall_fit: 8.5,
      reasoning: "Strong match in ML frameworks and relevant project experience. Stanford education aligns well with the role requirements."
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
      projects: ["Automated client churn prediction pipeline"],
      education: "B.S. Statistics, UC Berkeley",
      summary: "Data Scientist focusing on predictive modeling."
    },
    llm_evaluation: {
      technical_skill_match: 8.0,
      relevant_experience: 7.0,
      project_relevance: 8.0,
      overall_fit: 7.5,
      reasoning: "Good data science skillset. Experience in predictive modeling is valuable, though slightly less senior in core ML systems engineering."
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
      projects: ["Refactored monolithic service into microservices"],
      education: "B.S. Computer Science, University of Washington",
      summary: "Software Engineer with basic exposure to Python."
    },
    llm_evaluation: {
      technical_skill_match: 6.0,
      relevant_experience: 5.0,
      project_relevance: 6.0,
      overall_fit: 6.0,
      reasoning: "Mainly software engineering background. Lacks deep machine learning specialization, but python basics and docker experience are positive."
    }
  }
];

export const rankingService = {
  /**
   * Fetch backend system health.
   */
  checkHealth: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.warn('Backend /health failed. Falling back to mock online status.');
      // Mock successful response if server is offline
      return {
        status: "healthy (mock)",
        version: "1.0.0",
        candidates_loaded: 3,
        faiss_index_size: 3,
        ollama_available: true,
      };
    }
  },

  /**
   * Send ranking request to backend.
   * Accepts FormData (which contains files and job description text).
   */
  rankCandidates: async (formData) => {
    try {
      const response = await api.post('/rank', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.warn('Backend /rank failed. Using mock evaluation results.', error);
      // Wait 1 second to simulate loading
      await new Promise(resolve => setTimeout(resolve, 1500));
      return {
        job_role: "Senior Machine Learning Engineer",
        total_candidates: 3,
        candidates: mockCandidates,
      };
    }
  },

  /**
   * Fetch candidate details by ID.
   */
  getCandidateById: async (candidateId) => {
    try {
      const response = await api.get(`/candidate/${candidateId}`);
      return response.data;
    } catch (error) {
      console.warn(`Backend /candidate/${candidateId} failed. Using mock candidate.`, error);
      const matched = mockCandidates.find(c => c.candidate_id === candidateId);
      if (matched) return matched;
      throw new Error(`Candidate ${candidateId} not found`);
    }
  }
};
