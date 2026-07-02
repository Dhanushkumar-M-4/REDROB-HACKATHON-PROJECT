document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('ranking-form');
    const fileUpload = document.getElementById('file-upload');
    const uploadText = document.getElementById('upload-text');
    const systemStatus = document.getElementById('system-status');
    const statusText = document.getElementById('status-text');
    
    // Views
    const inputView = document.getElementById('input-view');
    const loadingView = document.getElementById('loading-view');
    const resultsView = document.getElementById('results-view');
    
    // Results
    const candidatesGrid = document.getElementById('candidates-grid');
    const jobRoleText = document.getElementById('job-role-text');
    const backBtn = document.getElementById('back-btn');
    
    // Modal
    const modal = document.getElementById('candidate-modal');
    const modalClose = document.getElementById('modal-close');
    const modalBody = document.getElementById('modal-body');

    let currentCandidates = [];

    // Initialize
    checkHealth();
    
    // Event Listeners
    fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadText.textContent = e.target.files[0].name;
            uploadText.style.color = 'var(--accent-primary)';
            uploadText.style.fontWeight = '600';
            // Clear textarea if file is uploaded
            document.getElementById('job-description').value = '';
        } else {
            uploadText.textContent = 'Choose a file or drag it here';
            uploadText.style.color = 'var(--text-secondary)';
            uploadText.style.fontWeight = 'normal';
        }
    });

    document.getElementById('job-description').addEventListener('input', () => {
        // Clear file upload if text is typed
        if (document.getElementById('job-description').value.trim() !== '') {
            fileUpload.value = '';
            uploadText.textContent = 'Choose a file or drag it here';
            uploadText.style.color = 'var(--text-secondary)';
            uploadText.style.fontWeight = 'normal';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const jdText = document.getElementById('job-description').value.trim();
        const file = fileUpload.files[0];
        
        if (!jdText && !file) {
            alert('Please provide a job description or upload a JD file.');
            return;
        }

        const formData = new FormData();
        if (file) {
            formData.append('file', file);
        } else {
            formData.append('job_description', jdText);
        }

        switchView(loadingView);

        try {
            const response = await fetch('http://localhost:8000/rank', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to rank candidates');
            }

            const data = await response.json();
            renderResults(data);
            switchView(resultsView);
        } catch (error) {
            console.error(error);
            alert(`Error: ${error.message}`);
            switchView(inputView);
        }
    });

    backBtn.addEventListener('click', () => {
        switchView(inputView);
        form.reset();
        uploadText.textContent = 'Choose a file or drag it here';
        uploadText.style.color = 'var(--text-secondary)';
        uploadText.style.fontWeight = 'normal';
    });

    modalClose.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Functions
    async function checkHealth() {
        try {
            const res = await fetch('http://localhost:8000/health');
            if (res.ok) {
                const data = await res.json();
                systemStatus.classList.add('healthy');
                systemStatus.classList.remove('error');
                statusText.textContent = `Online • ${data.candidates_loaded} candidates loaded`;
            } else {
                throw new Error();
            }
        } catch (e) {
            systemStatus.classList.add('error');
            systemStatus.classList.remove('healthy');
            statusText.textContent = 'Backend Offline';
        }
    }

    function switchView(view) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        view.classList.add('active');
    }

    function renderResults(data) {
        jobRoleText.textContent = data.job_role || 'Unknown Role';
        candidatesGrid.innerHTML = '';
        currentCandidates = data.candidates || [];
        
        if (currentCandidates.length === 0) {
            candidatesGrid.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1/-1; text-align: center;">No candidates found.</p>';
            return;
        }

        currentCandidates.forEach(cand => {
            const card = document.createElement('div');
            card.className = 'candidate-card';
            
            // Format scores safely
            const totalScore = cand.total_score ? cand.total_score.toFixed(1) : 'N/A';
            const llmScore = cand.llm_score ? cand.llm_score.toFixed(1) : '0.0';
            const expYears = cand.profile && cand.profile.experience_years ? cand.profile.experience_years.toFixed(1) : '0';
            
            card.innerHTML = `
                <div class="score-badge">${totalScore}</div>
                <div class="candidate-header">
                    <div>
                        <div class="candidate-name">${cand.profile?.name || 'Unknown Candidate'}</div>
                        <div class="candidate-id">${cand.candidate_id || 'ID N/A'}</div>
                    </div>
                </div>
                
                <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    ${cand.profile?.summary || 'No summary available.'}
                </p>
                
                <div class="candidate-stats">
                    <div class="stat">
                        <span class="stat-label">LLM Score</span>
                        <span class="stat-value">${llmScore} / 100</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Experience</span>
                        <span class="stat-value">${expYears} yrs</span>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => openCandidateModal(cand));
            candidatesGrid.appendChild(card);
        });
    }

    function openCandidateModal(cand) {
        const profile = cand.profile || {};
        const llm = cand.llm_evaluation || {};
        
        const skillsHtml = (profile.skills || []).map(s => `<span class="skill-tag">${s}</span>`).join('');
        const projectsHtml = (profile.projects || []).map(p => `<li>${p}</li>`).join('');
        
        let llmHtml = '';
        if (llm.reasoning && llm.reasoning !== 'LLM evaluation unavailable') {
            llmHtml = `
                <div class="detail-section">
                    <h4>AI Deep Evaluation Reasoning</h4>
                    <div class="reasoning-box">${llm.reasoning}</div>
                </div>
                <div class="detail-section">
                    <h4>Detailed AI Scores</h4>
                    <div class="score-grid">
                        <div class="score-item"><span class="stat-label">Technical Match</span><span class="stat-value">${llm.technical_skill_match || 0}/10</span></div>
                        <div class="score-item"><span class="stat-label">Experience Fit</span><span class="stat-value">${llm.relevant_experience || 0}/10</span></div>
                        <div class="score-item"><span class="stat-label">Project Relevance</span><span class="stat-value">${llm.project_relevance || 0}/10</span></div>
                        <div class="score-item"><span class="stat-label">Overall Fit</span><span class="stat-value">${llm.overall_fit || 0}/10</span></div>
                    </div>
                </div>
            `;
        } else {
            llmHtml = `
                <div class="detail-section">
                    <h4>AI Evaluation</h4>
                    <p style="color: var(--text-secondary); font-style: italic;">Detailed LLM reasoning is not available for this candidate.</p>
                </div>
            `;
        }

        modalBody.innerHTML = `
            <div class="modal-header">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h2 style="font-family: var(--font-heading); font-size: 2rem; margin-bottom: 0.5rem;">${profile.name || 'Unknown Candidate'}</h2>
                        <div class="candidate-id">${cand.candidate_id}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">Overall Match</div>
                        <div style="font-size: 2.5rem; font-weight: 700; color: var(--success); font-family: var(--font-heading); line-height: 1;">${cand.total_score ? cand.total_score.toFixed(1) : 'N/A'}</div>
                    </div>
                </div>
            </div>
            
            <div class="modal-body-content">
                ${llmHtml}
                
                <div class="detail-section">
                    <h4>Skills</h4>
                    <div class="skills-list">
                        ${skillsHtml || '<span style="color: var(--text-secondary);">No skills listed.</span>'}
                    </div>
                </div>
                
                <div class="detail-section" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <h4>Education & Certs</h4>
                        <p style="margin-bottom: 0.5rem;">${profile.education || 'Not specified'}</p>
                        ${profile.certifications && profile.certifications.length > 0 ? `<ul style="padding-left: 1.2rem; color: var(--text-secondary);">${profile.certifications.map(c => `<li>${c}</li>`).join('')}</ul>` : ''}
                    </div>
                    <div>
                        <h4>Notable Projects</h4>
                        ${projectsHtml ? `<ul style="padding-left: 1.2rem; color: var(--text-secondary);">${projectsHtml}</ul>` : '<p style="color: var(--text-secondary);">None specified</p>'}
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.add('active');
    }
});
