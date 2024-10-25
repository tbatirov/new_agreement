document.addEventListener('DOMContentLoaded', () => {
    const pads = ['signature1Pad', 'signature2Pad'];
    
    pads.forEach(padId => {
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 200;
        document.getElementById(padId).appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        let drawing = false;
        
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('touchstart', handleTouch);
        canvas.addEventListener('touchmove', handleTouch);
        canvas.addEventListener('touchend', stopDrawing);
        
        function startDrawing(e) {
            drawing = true;
            draw(e);
        }
        
        function draw(e) {
            if (!drawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX || e.touches[0].clientX) - rect.left;
            const y = (e.clientY || e.touches[0].clientY) - rect.top;
            
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineTo(x, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, y);
        }
        
        function stopDrawing() {
            drawing = false;
            ctx.beginPath();
            document.getElementById(padId.replace('Pad', 'Data')).value = canvas.toDataURL();
        }
        
        function handleTouch(e) {
            e.preventDefault();
            const touch = e.type === 'touchstart' ? startDrawing : draw;
            touch(e);
        }
    });
});

function clearSignature(padId) {
    const canvas = document.querySelector(`#${padId} canvas`);
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    document.getElementById(padId.replace('Pad', 'Data')).value = '';
}
