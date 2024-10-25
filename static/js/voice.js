document.addEventListener('DOMContentLoaded', () => {
    // Find required DOM elements
    const elements = {
        startButton: document.getElementById('startVoice'),
        stopButton: document.getElementById('stopVoice'),
        contentArea: document.getElementById('content')
    };
    
    // Check if all required elements exist
    const missingElements = Object.entries(elements)
        .filter(([key, element]) => !element)
        .map(([key]) => key);
        
    if (missingElements.length > 0) {
        console.error('Voice input initialization failed. Missing elements:', missingElements.join(', '));
        return;
    }
    
    const { startButton, stopButton, contentArea } = elements;
    
    // Create status container only if content area exists
    if (contentArea && contentArea.parentNode) {
        const statusContainer = document.createElement('div');
        statusContainer.className = 'mb-3';
        statusContainer.innerHTML = `
            <div id="voiceStatus" class="alert alert-info d-none"></div>
            <div id="permissionStatus" class="d-flex align-items-center gap-2 mb-2">
                <i class="bi bi-mic-mute text-danger"></i>
                <span>Checking microphone permissions...</span>
            </div>
            <button type="button" id="retryPermission" class="btn btn-outline-primary d-none">
                <i class="bi bi-arrow-clockwise"></i> Retry Microphone Access
            </button>
        `;
        contentArea.parentNode.insertBefore(statusContainer, contentArea);
    }
    
    const permissionStatus = document.getElementById('permissionStatus');
    const retryButton = document.getElementById('retryPermission');
    const voiceStatus = document.getElementById('voiceStatus');
    
    let recognition = null;
    
    // Check for HTTPS context
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '0.0.0.0') {
        showStatus('Speech recognition requires HTTPS for security reasons.', 'warning');
        updatePermissionStatus('blocked', 'HTTPS required');
        return;
    }
    
    function showStatus(message, type) {
        if (!voiceStatus) return;
        voiceStatus.className = `alert alert-${type}`;
        voiceStatus.textContent = message;
        voiceStatus.classList.remove('d-none');
    }
    
    function updatePermissionStatus(status, message) {
        if (!permissionStatus) return;
        
        const statusMap = {
            'granted': { icon: 'bi-mic-fill text-success', text: 'Microphone access granted' },
            'denied': { icon: 'bi-mic-mute text-danger', text: 'Microphone access denied' },
            'blocked': { icon: 'bi-shield-exclamation text-warning', text: message || 'Microphone access blocked' },
            'error': { icon: 'bi-exclamation-triangle text-danger', text: message || 'Error accessing microphone' }
        };
        
        const statusInfo = statusMap[status];
        permissionStatus.innerHTML = `
            <i class="bi ${statusInfo.icon}"></i>
            <span>${statusInfo.text}</span>
        `;
        
        if (status === 'granted' && startButton) {
            startButton.disabled = false;
            if (retryButton) retryButton.classList.add('d-none');
        } else {
            disableVoiceInput();
        }
    }
    
    function showRetryButton() {
        if (!retryButton) return;
        retryButton.classList.remove('d-none');
        showStatus('Please allow microphone access in your browser settings or click Retry.', 'warning');
    }
    
    if (retryButton) {
        retryButton.addEventListener('click', async () => {
            retryButton.disabled = true;
            showStatus('Requesting microphone access...', 'info');
            await checkMicrophonePermission();
            retryButton.disabled = false;
        });
    }
    
    async function checkMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            updatePermissionStatus('granted');
            initializeSpeechRecognition();
            return true;
        } catch (error) {
            console.error('Microphone permission error:', error);
            if (error.name === 'NotAllowedError') {
                updatePermissionStatus('denied');
                showRetryButton();
            } else {
                updatePermissionStatus('error', error.message);
            }
            return false;
        }
    }
    
    function initializeSpeechRecognition() {
        if (!('webkitSpeechRecognition' in window)) {
            showStatus('Speech recognition is not supported in your browser. Please use Chrome.', 'warning');
            updatePermissionStatus('blocked', 'Browser not supported');
            return;
        }
        
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onstart = () => {
            showStatus('Listening... Speak clearly into your microphone.', 'info');
            if (startButton) {
                startButton.innerHTML = '<i class="bi bi-mic-fill"></i> Recording...';
                startButton.classList.replace('btn-secondary', 'btn-success');
            }
        };
        
        recognition.onresult = (event) => {
            if (!contentArea) return;
            
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                }
            }
            if (finalTranscript) {
                contentArea.value += (contentArea.value ? ' ' : '') + finalTranscript;
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            
            switch (event.error) {
                case 'not-allowed':
                    updatePermissionStatus('denied');
                    showRetryButton();
                    break;
                case 'no-speech':
                    showStatus('No speech detected. Please try speaking again.', 'warning');
                    break;
                case 'network':
                    showStatus('Network error occurred. Please check your internet connection.', 'warning');
                    break;
                default:
                    showStatus('An error occurred with speech recognition. Please try again.', 'warning');
            }
            
            stopVoiceInput();
        };
        
        recognition.onend = () => {
            stopVoiceInput();
            showStatus('Voice input stopped.', 'info');
        };
    }
    
    if (startButton) {
        startButton.addEventListener('click', () => {
            if (recognition) {
                try {
                    recognition.start();
                    startButton.disabled = true;
                    if (stopButton) stopButton.disabled = false;
                } catch (error) {
                    showStatus('Error starting voice input. Please try again.', 'danger');
                    console.error('Start error:', error);
                }
            }
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', stopVoiceInput);
    }
    
    function stopVoiceInput() {
        if (recognition) {
            try {
                recognition.stop();
            } catch (error) {
                console.error('Stop error:', error);
            }
            if (startButton) {
                startButton.disabled = false;
                startButton.innerHTML = '<i class="bi bi-mic-fill"></i> Start Voice Input';
                startButton.classList.replace('btn-success', 'btn-secondary');
            }
            if (stopButton) {
                stopButton.disabled = true;
            }
        }
    }
    
    function disableVoiceInput() {
        if (startButton) startButton.disabled = true;
        if (stopButton) stopButton.disabled = true;
    }
    
    // Initialize permission check
    checkMicrophonePermission();
});
