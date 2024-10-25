class TemplateLoader {
    constructor() {
        this.elements = null;
        this.templates = {};
        this.maxRetries = 3;
        this.retryDelay = 1000;
        
        // Initialize after DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        try {
            this.findAndValidateElements();
            this.initializeEventListeners();
            this.loadTemplates();
        } catch (error) {
            console.error('Template loader initialization failed:', error);
            this.showFeedback('Error initializing template loader. Please refresh the page.', 'danger');
        }
    }
    
    findAndValidateElements() {
        this.elements = {
            templateSelect: document.getElementById('templateSelect'),
            templateFeedback: document.getElementById('templateFeedback'),
            loadTemplateBtn: document.getElementById('loadTemplate'),
            contentArea: document.getElementById('content'),
            previewContent: document.getElementById('previewContent'),
            previewSpinner: document.getElementById('previewSpinner'),
            loadingSpinner: document.querySelector('#loadTemplate .spinner-border')
        };
        
        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);
            
        if (missingElements.length > 0) {
            throw new Error(`Missing required elements: ${missingElements.join(', ')}`);
        }
    }
    
    showFeedback(message, type, timeout = 5000) {
        if (!this.elements?.templateFeedback) return;
        
        this.elements.templateFeedback.textContent = message;
        this.elements.templateFeedback.className = `alert alert-${type}`;
        this.elements.templateFeedback.classList.remove('d-none');
        
        if (timeout) {
            setTimeout(() => {
                if (this.elements?.templateFeedback) {
                    this.elements.templateFeedback.classList.add('d-none');
                }
            }, timeout);
        }
    }
    
    setLoadingState(isLoading) {
        if (!this.elements) return;
        
        this.elements.loadTemplateBtn.disabled = isLoading;
        this.elements.loadingSpinner?.classList.toggle('d-none', !isLoading);
        
        if (isLoading) {
            this.elements.previewSpinner?.classList.remove('d-none');
        } else {
            this.elements.previewSpinner?.classList.add('d-none');
        }
    }
    
    async loadTemplates() {
        try {
            this.setLoadingState(true);
            this.showFeedback('Loading templates...', 'info');
            
            const response = await this.fetchWithRetry('/templates');
            if (!Array.isArray(response)) {
                throw new Error('Invalid template data format');
            }
            
            this.templates = response.reduce((acc, template) => {
                if (!template.id || !template.name) {
                    console.error('Invalid template format:', template);
                    return acc;
                }
                acc[template.id] = template;
                return acc;
            }, {});
            
            this.updateTemplateSelect();
            this.showFeedback('Templates loaded successfully!', 'success');
            console.log('Templates loaded:', this.templates);
            
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showFeedback('Error loading templates. Please try again.', 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    updateTemplateSelect() {
        if (!this.elements?.templateSelect) return;
        
        // Clear existing options except the default
        while (this.elements.templateSelect.options.length > 1) {
            this.elements.templateSelect.remove(1);
        }
        
        // Add new options
        Object.values(this.templates).forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            this.elements.templateSelect.appendChild(option);
        });
    }
    
    async fetchWithRetry(url, options = {}, retries = 0) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Attempt ${retries + 1} failed:`, error);
            if (retries < this.maxRetries) {
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.fetchWithRetry(url, options, retries + 1);
            }
            throw error;
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.content;
        if (!token) {
            console.warn('CSRF token not found. Please ensure the meta tag is present.');
        }
        return token || '';
    }
    
    initializeEventListeners() {
        if (!this.elements) return;
        
        if (this.elements.loadTemplateBtn && this.elements.templateSelect) {
            this.elements.loadTemplateBtn.addEventListener('click', () => this.loadSelectedTemplate());
            this.elements.templateSelect.addEventListener('change', () => {
                if (this.elements.templateSelect.value) {
                    this.loadSelectedTemplate();
                }
            });
        }
        
        if (this.elements.contentArea) {
            this.elements.contentArea.addEventListener('input', () => this.handleContentChange());
        }
    }
    
    async loadSelectedTemplate() {
        if (!this.elements?.templateSelect || !this.elements?.contentArea) return;
        
        const selectedTemplate = this.elements.templateSelect.value;
        if (!selectedTemplate) {
            this.showFeedback('Please select a template first.', 'warning');
            return;
        }
        
        try {
            this.setLoadingState(true);
            this.showFeedback('Loading template...', 'info');
            
            const data = await this.fetchWithRetry(`/templates/${selectedTemplate}`);
            if (!data.content) {
                throw new Error('Invalid template content');
            }
            
            this.elements.contentArea.value = data.content;
            if (this.elements.previewContent) {
                this.elements.previewContent.innerHTML = data.content.replace(/\n/g, '<br>');
            }
            
            this.showFeedback('Template loaded successfully!', 'success');
            this.validateContent();
            
        } catch (error) {
            console.error('Error loading template:', error);
            this.showFeedback('Error loading template content. Please try again.', 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    handleContentChange() {
        if (!this.elements?.contentArea || !this.elements?.previewContent) return;
        
        const content = this.elements.contentArea.value.trim();
        this.elements.previewContent.innerHTML = content ? 
            content.replace(/\n/g, '<br>') : 
            '<p class="text-muted">Start typing to see the preview...</p>';
            
        this.validateContent();
    }
    
    validateContent() {
        if (!this.elements?.contentArea) return;
        
        const content = this.elements.contentArea.value.trim();
        const isValid = content.length >= 10; // Minimum content length
        
        this.elements.contentArea.classList.toggle('is-valid', isValid);
        this.elements.contentArea.classList.toggle('is-invalid', !isValid);
        
        return isValid;
    }
}

// Export for use in other modules
window.TemplateLoader = TemplateLoader;
