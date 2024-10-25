class TemplateLoader {
    constructor() {
        this.elements = null;
        this.templates = {};
        this.maxRetries = 3;
        this.retryDelay = 1000;
        this.initialized = false;
        this.initializationError = null;
        
        // Initialize after DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    async initialize() {
        try {
            console.log('Initializing template loader...');
            await this.findAndValidateElements();
            await this.initializeEventListeners();
            await this.loadTemplates();
            this.initialized = true;
            console.log('Template loader initialized successfully');
        } catch (error) {
            this.initializationError = error;
            console.error('Template loader initialization failed:', error);
            this.showError('Error initializing template loader', error);
        }
    }
    
    async findAndValidateElements() {
        console.log('Finding and validating DOM elements...');
        
        // Required elements configuration
        const requiredElements = {
            templateSelect: { id: 'templateSelect', description: 'Template selection dropdown' },
            templateFeedback: { id: 'templateFeedback', description: 'Template feedback container' },
            loadTemplateBtn: { id: 'loadTemplate', description: 'Load template button' },
            contentArea: { id: 'content', description: 'Agreement content textarea' },
            previewContent: { id: 'previewContent', description: 'Preview content container' },
            previewSpinner: { id: 'previewSpinner', description: 'Preview loading spinner' }
        };
        
        // Find all elements
        this.elements = {};
        const missingElements = [];
        
        for (const [key, config] of Object.entries(requiredElements)) {
            const element = document.getElementById(config.id);
            if (element) {
                this.elements[key] = element;
            } else {
                missingElements.push(`${config.description} (${config.id})`);
            }
        }
        
        // Additional UI elements
        this.elements.loadingSpinner = this.elements.loadTemplateBtn?.querySelector('.spinner-border');
        this.elements.retryButton = document.createElement('button');
        this.elements.retryButton.className = 'btn btn-outline-primary btn-sm mt-2 d-none';
        this.elements.retryButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Retry Loading Templates';
        
        if (this.elements.templateFeedback) {
            this.elements.templateFeedback.parentNode.insertBefore(
                this.elements.retryButton,
                this.elements.templateFeedback.nextSibling
            );
        }
        
        if (missingElements.length > 0) {
            throw new Error(`Missing required elements: ${missingElements.join(', ')}`);
        }
        
        console.log('All required DOM elements found');
    }
    
    showError(message, error = null) {
        console.error(message, error);
        
        // Show user-friendly error message
        this.showFeedback(
            `${message}. ${error?.message || 'Please try again or refresh the page.'}`,
            'danger',
            0
        );
        
        // Show retry button
        if (this.elements?.retryButton) {
            this.elements.retryButton.classList.remove('d-none');
        }
        
        // Disable template selection until error is resolved
        if (this.elements?.templateSelect) {
            this.elements.templateSelect.disabled = true;
        }
        
        // Update button state
        if (this.elements?.loadTemplateBtn) {
            this.elements.loadTemplateBtn.disabled = true;
        }
    }
    
    async retryInitialization() {
        console.log('Retrying template loader initialization...');
        
        if (this.elements?.retryButton) {
            this.elements.retryButton.disabled = true;
        }
        
        try {
            this.initialized = false;
            this.initializationError = null;
            await this.initialize();
            
            // Re-enable UI elements on success
            if (this.elements?.templateSelect) {
                this.elements.templateSelect.disabled = false;
            }
            if (this.elements?.loadTemplateBtn) {
                this.elements.loadTemplateBtn.disabled = false;
            }
            if (this.elements?.retryButton) {
                this.elements.retryButton.classList.add('d-none');
            }
            
            this.showFeedback('Template loader reinitialized successfully!', 'success');
        } catch (error) {
            console.error('Retry initialization failed:', error);
            if (this.elements?.retryButton) {
                this.elements.retryButton.disabled = false;
            }
        }
    }
    
    showFeedback(message, type = 'info', timeout = 5000) {
        if (!this.elements?.templateFeedback) return;
        
        // Clear existing feedback
        while (this.elements.templateFeedback.firstChild) {
            this.elements.templateFeedback.firstChild.remove();
        }
        
        // Create feedback alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} mb-0`;
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi ${this.getFeedbackIcon(type)} me-2"></i>
                <div>${message}</div>
            </div>
        `;
        
        this.elements.templateFeedback.appendChild(alert);
        this.elements.templateFeedback.classList.remove('d-none');
        
        if (timeout > 0) {
            setTimeout(() => {
                if (this.elements?.templateFeedback?.contains(alert)) {
                    alert.remove();
                    if (!this.elements.templateFeedback.firstChild) {
                        this.elements.templateFeedback.classList.add('d-none');
                    }
                }
            }, timeout);
        }
    }
    
    getFeedbackIcon(type) {
        const icons = {
            success: 'bi-check-circle-fill',
            danger: 'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-circle-fill',
            info: 'bi-info-circle-fill'
        };
        return icons[type] || icons.info;
    }
    
    setLoadingState(isLoading) {
        if (!this.elements) return;
        
        this.elements.loadTemplateBtn.disabled = isLoading;
        this.elements.loadingSpinner?.classList.toggle('d-none', !isLoading);
        this.elements.previewSpinner?.classList.toggle('d-none', isLoading);
        
        if (isLoading) {
            this.showFeedback('Loading template...', 'info');
        }
    }
    
    async loadTemplates() {
        if (!this.initialized && !this.elements) {
            throw new Error('Template loader not properly initialized');
        }
        
        try {
            this.setLoadingState(true);
            console.log('Loading templates...');
            
            const response = await this.fetchWithRetry('/templates');
            if (!Array.isArray(response)) {
                throw new Error('Invalid template data format received from server');
            }
            
            this.templates = response.reduce((acc, template) => {
                if (!this.validateTemplateData(template)) {
                    console.warn('Invalid template data:', template);
                    return acc;
                }
                acc[template.id] = template;
                return acc;
            }, {});
            
            await this.updateTemplateSelect();
            this.showFeedback('Templates loaded successfully!', 'success');
            console.log('Templates loaded:', Object.keys(this.templates).length);
            
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showError('Error loading templates', error);
            throw error;
        } finally {
            this.setLoadingState(false);
        }
    }
    
    validateTemplateData(template) {
        const requiredFields = ['id', 'name'];
        return requiredFields.every(field => {
            const hasField = template.hasOwnProperty(field) && template[field];
            if (!hasField) {
                console.warn(`Template missing required field: ${field}`, template);
            }
            return hasField;
        });
    }
    
    async updateTemplateSelect() {
        if (!this.elements?.templateSelect) return;
        
        console.log('Updating template select options...');
        
        // Clear existing options except the default
        while (this.elements.templateSelect.options.length > 1) {
            this.elements.templateSelect.remove(1);
        }
        
        // Add new options
        const fragment = document.createDocumentFragment();
        Object.values(this.templates).forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            fragment.appendChild(option);
        });
        
        this.elements.templateSelect.appendChild(fragment);
        console.log('Template select options updated');
    }
    
    async fetchWithRetry(url, options = {}, retries = 0) {
        const requestOptions = {
            ...options,
            headers: {
                ...options.headers,
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken(),
                'Accept': 'application/json'
            }
        };
        
        try {
            console.log(`Fetching ${url} (attempt ${retries + 1}/${this.maxRetries + 1})`);
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType?.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType?.includes('application/json')) {
                throw new Error('Invalid response format: expected JSON');
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Fetch attempt ${retries + 1} failed:`, error);
            
            if (retries < this.maxRetries) {
                const delay = this.retryDelay * Math.pow(2, retries);
                console.log(`Retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
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
    
    async initializeEventListeners() {
        if (!this.elements) return;
        
        console.log('Initializing event listeners...');
        
        // Template selection and loading
        if (this.elements.loadTemplateBtn && this.elements.templateSelect) {
            this.elements.loadTemplateBtn.addEventListener('click', () => this.loadSelectedTemplate());
            this.elements.templateSelect.addEventListener('change', () => {
                if (this.elements.templateSelect.value) {
                    this.loadSelectedTemplate();
                }
            });
        }
        
        // Content preview
        if (this.elements.contentArea) {
            this.elements.contentArea.addEventListener('input', () => this.handleContentChange());
        }
        
        // Retry button
        if (this.elements.retryButton) {
            this.elements.retryButton.addEventListener('click', () => this.retryInitialization());
        }
        
        console.log('Event listeners initialized');
    }
    
    async loadSelectedTemplate() {
        if (!this.initialized || !this.elements?.templateSelect || !this.elements?.contentArea) {
            this.showError('Template loader not properly initialized');
            return;
        }
        
        const selectedTemplate = this.elements.templateSelect.value;
        if (!selectedTemplate) {
            this.showFeedback('Please select a template first.', 'warning');
            return;
        }
        
        try {
            this.setLoadingState(true);
            
            const data = await this.fetchWithRetry(`/templates/${selectedTemplate}`);
            if (!data.content) {
                throw new Error('Invalid template content received from server');
            }
            
            this.elements.contentArea.value = data.content;
            if (this.elements.previewContent) {
                this.elements.previewContent.innerHTML = this.formatPreviewContent(data.content);
            }
            
            this.showFeedback('Template loaded successfully!', 'success');
            this.validateContent();
            
        } catch (error) {
            console.error('Error loading template:', error);
            this.showError('Error loading template content', error);
        } finally {
            this.setLoadingState(false);
        }
    }
    
    formatPreviewContent(content) {
        if (!content.trim()) {
            return '<p class="text-muted">Start typing to see the preview...</p>';
        }
        return content.replace(/\n/g, '<br>');
    }
    
    handleContentChange() {
        if (!this.elements?.contentArea || !this.elements?.previewContent) return;
        
        const content = this.elements.contentArea.value.trim();
        this.elements.previewContent.innerHTML = this.formatPreviewContent(content);
        this.validateContent();
    }
    
    validateContent() {
        if (!this.elements?.contentArea) return;
        
        const content = this.elements.contentArea.value.trim();
        const minLength = 10;
        const isValid = content.length >= minLength;
        
        this.elements.contentArea.classList.toggle('is-valid', isValid);
        this.elements.contentArea.classList.toggle('is-invalid', !isValid);
        
        return isValid;
    }
}

// Initialize template loader
window.templateLoader = new TemplateLoader();
