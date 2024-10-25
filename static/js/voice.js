document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startVoice');
    const stopButton = document.getElementById('stopVoice');
    const contentArea = document.getElementById('content');
    
    let recognition = null;
    
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                }
            }
            if (finalTranscript) {
                contentArea.value += ' ' + finalTranscript;
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            stopVoiceInput();
        };
    }
    
    startButton.addEventListener('click', () => {
        if (recognition) {
            recognition.start();
            startButton.disabled = true;
            stopButton.disabled = false;
        }
    });
    
    stopButton.addEventListener('click', stopVoiceInput);
    
    function stopVoiceInput() {
        if (recognition) {
            recognition.stop();
            startButton.disabled = false;
            stopButton.disabled = true;
        }
    }
});
