document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startVoice');
    const stopButton = document.getElementById('stopVoice');
    const contentArea = document.getElementById('content');
    
    // Add status message div
    const statusDiv = document.createElement('div');
    statusDiv.className = 'alert alert-info d-none';
    statusDiv.id = 'voiceStatus';
    contentArea.parentNode.insertBefore(statusDiv, contentArea);
    
    let recognition = null;
    
    // Check for HTTPS context
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '0.0.0.0') {
        showStatus('Speech recognition requires HTTPS for security reasons.', 'warning');
        disableVoiceInput();
        return;
    }
    
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onstart = () => {
            showStatus('Listening... Speak clearly into your microphone.', 'info');
        };
        
        recognition.onresult = (event) => {
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
                    showStatus('Microphone access denied. Please allow microphone access in your browser settings and try again.', 'danger');
                    disableVoiceInput();
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
    } else {
        showStatus('Speech recognition is not supported in your browser. Please use a modern browser like Chrome.', 'warning');
        disableVoiceInput();
    }
    
    startButton.addEventListener('click', () => {
        if (recognition) {
            // Add instructions before starting
            showStatus('Please allow microphone access when prompted by your browser.', 'info');
            try {
                recognition.start();
                startButton.disabled = true;
                stopButton.disabled = false;
            } catch (error) {
                showStatus('Error starting voice input. Please try again.', 'danger');
                console.error('Start error:', error);
            }
        }
    });
    
    stopButton.addEventListener('click', stopVoiceInput);
    
    function stopVoiceInput() {
        if (recognition) {
            try {
                recognition.stop();
            } catch (error) {
                console.error('Stop error:', error);
            }
            startButton.disabled = false;
            stopButton.disabled = true;
        }
    }
    
    function showStatus(message, type) {
        const statusDiv = document.getElementById('voiceStatus');
        statusDiv.className = `alert alert-${type} mt-2`;
        statusDiv.textContent = message;
        statusDiv.classList.remove('d-none');
    }
    
    function disableVoiceInput() {
        startButton.disabled = true;
        stopButton.disabled = true;
    }
});
