class TemplateLoader {
    constructor(maxRetries = 3, retryDelay = 1000) {
        // Initialize with null values
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;
        this.templates = {};
        
        // Find required DOM elements
        const elements = this.findRequiredElements();
        if (!elements) {
            console.error('Required DOM elements not found for TemplateLoader');
            return;
        }
        
        Object.assign(this, elements);
        
        // Initialize event listeners only if elements exist
        this.initializeEventListeners();
        
        // Load templates on initialization
        this.initializeTemplates();
    }
    
    findRequiredElements() {
        const elements = {
            templateSelect: document.getElementById('templateSelect'),
            templateFeedback: document.getElementById('templateFeedback'),
            loadTemplateBtn: document.getElementById('loadTemplate'),
            contentArea: document.getElementById('content'),
            previewContent: document.getElementById('previewContent'),
            previewSpinner: document.getElementById('previewSpinner')
        };
        
        // Check if all required elements exist
        const missingElements = Object.entries(elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);
            
        if (missingElements.length > 0) {
            console.error('Missing required elements:', missingElements.join(', '));
            return null;
        }
        
        return elements;
    }
    
    initializeEventListeners() {
        if (this.loadTemplateBtn && this.templateSelect) {
            this.loadTemplateBtn.addEventListener('click', () => this.loadSelectedTemplate());
            this.templateSelect.addEventListener('change', () => this.loadSelectedTemplate());
        }
    }

    showFeedback(message, type) {
        if (!this.templateFeedback) return;
        
        this.templateFeedback.textContent = message;
        this.templateFeedback.className = `alert alert-${type}`;
        this.templateFeedback.classList.remove('d-none');
        setTimeout(() => {
            if (this.templateFeedback) {
                this.templateFeedback.classList.add('d-none');
            }
        }, 5000);
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
        if (!this.templateSelect) return;
        
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
        if (!this.templateSelect) return;
        
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
        if (!this.templateSelect || !this.contentArea || !this.previewContent) return;
        
        const selectedTemplate = this.templateSelect.value;
        if (!selectedTemplate) return;
        
        try {
            this.showFeedback('Loading template...', 'info');
            if (this.previewSpinner) {
                this.previewSpinner.classList.remove('d-none');
            }
            
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
            if (this.previewSpinner) {
                this.previewSpinner.classList.add('d-none');
            }
        }
    }
}

// Don't initialize here - moved to create_agreement.html
