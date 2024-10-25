class TemplateLoader {
    constructor(maxRetries = 3, retryDelay = 1000) {
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;
        this.templates = {};
        this.templateSelect = document.getElementById('templateSelect');
        this.templateFeedback = document.getElementById('templateFeedback');
        this.loadTemplateBtn = document.getElementById('loadTemplate');
        this.contentArea = document.getElementById('content');
        this.previewContent = document.getElementById('previewContent');
        this.previewSpinner = document.getElementById('previewSpinner');
        
        // Initialize event listeners
        this.loadTemplateBtn.addEventListener('click', () => this.loadSelectedTemplate());
        this.templateSelect.addEventListener('change', () => this.loadSelectedTemplate());
        
        // Load templates on initialization
        this.initializeTemplates();
    }

    showFeedback(message, type) {
        this.templateFeedback.textContent = message;
        this.templateFeedback.className = `alert alert-${type}`;
        this.templateFeedback.classList.remove('d-none');
        setTimeout(() => this.templateFeedback.classList.add('d-none'), 5000);
    }

    async fetchWithRetry(url, options = {}, retries = 0) {
        try {
            const response = await fetch(url, options);
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

    async initializeTemplates() {
        try {
            this.showFeedback('Loading templates...', 'info');
            const templatesData = await this.fetchWithRetry('/templates');
            
            // Verify template format
            if (!Array.isArray(templatesData)) {
                throw new Error('Invalid template data format');
            }
            
            this.templates = templatesData.reduce((acc, template) => {
                if (!template.id || !template.name) {
                    console.error('Invalid template format:', template);
                    return acc;
                }
                acc[template.id] = template;
                return acc;
            }, {});
            
            // Update select options
            this.updateTemplateSelect();
            this.showFeedback('Templates loaded successfully!', 'success');
            console.log('Templates loaded:', this.templates);
            
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showFeedback('Error loading templates. Please try again.', 'danger');
        }
    }

    updateTemplateSelect() {
        // Clear existing options except the default
        while (this.templateSelect.options.length > 1) {
            this.templateSelect.remove(1);
        }
        
        // Add new options
        Object.values(this.templates).forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            this.templateSelect.appendChild(option);
        });
    }

    async loadSelectedTemplate() {
        const selectedTemplate = this.templateSelect.value;
        if (!selectedTemplate) return;
        
        try {
            this.showFeedback('Loading template...', 'info');
            this.previewSpinner.classList.remove('d-none');
            
            const data = await this.fetchWithRetry(`/templates/${selectedTemplate}`);
            if (!data.content) {
                throw new Error('Invalid template content');
            }
            
            this.contentArea.value = data.content;
            this.previewContent.innerHTML = data.content.replace(/\n/g, '<br>');
            this.showFeedback('Template loaded successfully!', 'success');
            
        } catch (error) {
            console.error('Error loading template:', error);
            this.showFeedback('Error loading template content. Please try again.', 'danger');
        } finally {
            this.previewSpinner.classList.add('d-none');
        }
    }
}

// Initialize template loader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.templateLoader = new TemplateLoader();
});
