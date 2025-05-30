// DOM Elements
const askForm = document.getElementById('askForm');
const generateForm = document.getElementById('generateForm');
const askResult = document.getElementById('askResult');
const codeOutput = document.getElementById('codeOutput');

// Initialize clipboard.js for code copy functionality
new ClipboardJS('.copy-btn');

// Handle ask form submission with streaming
if (askForm) {
    askForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = document.getElementById('question').value.trim();
        if (!question) return;
        
        const submitBtn = askForm.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const spinner = submitBtn.querySelector('.loading-spinner');
        
        // Show loading state
        btnText.textContent = 'Asking...';
        spinner.style.display = 'inline-block';
        submitBtn.disabled = true;
        
        // Clear previous results/errors
        askResult.innerHTML = '';
        askResult.style.display = 'block';
        const errorElement = document.getElementById('askError');
        if (errorElement) errorElement.remove();
        
        // Create a new paragraph for the response
        const responseParagraph = document.createElement('div');
        responseParagraph.className = 'prose max-w-none';
        askResult.appendChild(responseParagraph);
        
        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ question })
            });
            
            if (!response.ok) {
                const errorData = await response.text();
                let errorMessage = `Error: ${response.status}`;
                try {
                    const jsonError = JSON.parse(errorData);
                    errorMessage = jsonError.error || errorMessage;
                } catch (e) {
                    errorMessage = errorData || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            if (!response.body) {
                throw new Error('No response body received');
            }
            
            // Process the streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                // Decode the chunk and process it
                buffer += decoder.decode(value, { stream: true });
                
                // Process each complete event
                const events = buffer.split('\n\n');
                buffer = events.pop() || ''; // Save incomplete event for next iteration
                
                for (const event of events) {
                    try {
                        if (!event.startsWith('data: ')) continue;
                        
                        const data = JSON.parse(event.slice(6).trim()); // Remove 'data: ' prefix and trim
                        
                        if (data && typeof data === 'object') {
                            if (data.error) {
                                throw new Error(data.error);
                            }
                            if (data.response) {
                                // Sanitize and append the new text to the response
                                const sanitized = data.response
                                    .replace(/&/g, '&amp;')
                                    .replace(/</g, '&lt;')
                                    .replace(/>/g, '&gt;');
                                
                                // Only update the DOM if we have actual content
                                if (sanitized.trim()) {
                                    responseParagraph.innerHTML += sanitized;
                                    // Scroll to the bottom
                                    responseParagraph.scrollIntoView({ behavior: 'smooth', block: 'end' });
                                }
                            }
                        }
                    } catch (e) {
                        console.error('Error processing event:', e);
                        // Don't throw here, continue processing other events
                    }
                }
            }
            
            // Apply syntax highlighting to any code blocks
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
            
        } catch (error) {
            console.error('Error:', error);
            showError(askForm, error.message || 'Failed to get a response. Please try again.');
        } finally {
            // Reset button state
            btnText.textContent = 'Ask Question';
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    });
}

// Handle generate form submission
if (generateForm) {
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const prompt = document.getElementById('prompt').value.trim();
        const language = document.getElementById('language').value;
        const framework = document.getElementById('framework').value;
        
        if (!prompt) return;
        
        const submitBtn = generateForm.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const spinner = submitBtn.querySelector('.loading-spinner');
        
        // Show loading state
        btnText.textContent = 'Generating...';
        spinner.style.display = 'inline-block';
        submitBtn.disabled = true;
        
        // Clear previous results/errors
        const generateResult = document.getElementById('generateResult');
        generateResult.style.display = 'none';
        const errorElement = document.getElementById('generateError');
        if (errorElement) errorElement.remove();
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ 
                    prompt,
                    language,
                    framework 
                })
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Display the generated code
            const codeBlock = createCodeBlock(data.code, language);
            codeOutput.innerHTML = '';
            codeOutput.appendChild(codeBlock);
            generateResult.style.display = 'block';
            
            // Scroll to the result
            generateResult.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error:', error);
            showError(generateForm, 'Failed to generate code. Please try again.');
        } finally {
            // Reset button state
            btnText.textContent = 'Generate Code';
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    });
}

// Helper function to create a code block with copy button
function createCodeBlock(code, language) {
    const container = document.createElement('div');
    container.className = 'code-block';
    
    const header = document.createElement('div');
    header.className = 'code-header';
    
    const langSpan = document.createElement('span');
    langSpan.className = 'code-language';
    langSpan.textContent = language || 'code';
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.setAttribute('data-clipboard-text', code);
    copyBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
        </svg>
        Copy
    `;
    
    header.appendChild(langSpan);
    header.appendChild(copyBtn);
    
    const pre = document.createElement('pre');
    const codeElement = document.createElement('code');
    codeElement.className = language ? `language-${language}` : '';
    codeElement.textContent = code;
    
    pre.appendChild(codeElement);
    container.appendChild(header);
    container.appendChild(pre);
    
    // Apply syntax highlighting
    hljs.highlightBlock(codeElement);
    
    // Add copy feedback
    copyBtn.addEventListener('click', () => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Copied!
        `;
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    });
    
    return container;
}

// Helper function to show error messages
function showError(formElement, message) {
    const errorDiv = document.createElement('div');
    errorDiv.id = `${formElement.id}Error`;
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="error-text">${message}</span>
    `;
    
    formElement.parentNode.insertBefore(errorDiv, formElement.nextSibling);
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}

// Initialize clipboard.js
new ClipboardJS('.copy-btn');
