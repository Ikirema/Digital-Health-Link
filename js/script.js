document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const dragArea = document.getElementById('drag-area');
    const imageContainer = document.getElementById('image-container');
    const detectionCanvas = document.getElementById('detectionCanvas');
    const detectionsList = document.getElementById('detections');
    
    // Drag and Drop functionality
    dragArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        dragArea.style.backgroundColor = '#e0e0e0';
    });

    dragArea.addEventListener('dragleave', () => {
        dragArea.style.backgroundColor = '';
    });

    dragArea.addEventListener('drop', (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file && file.type.startsWith("image")) {
            processImage(file);
        }
    });

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file && file.type.startsWith("image")) {
            processImage(file);
        }
    });

    const processImage = (file) => {
        const reader = new FileReader();
        reader.onload = function (e) {
            const img = new Image();
            img.src = e.target.result;
            img.onload = function () {
                imageContainer.innerHTML = '<img id="uploadedImage" src="' + img.src + '" alt="Uploaded Image" />';
                detectObjects(img);
            };
        };
        reader.readAsDataURL(file);
    };

    const detectObjects = async (img) => {
        // Display the canvas and clear previous results
        detectionCanvas.style.display = 'block';
        detectionsList.innerHTML = '';
        const ctx = detectionCanvas.getContext('2d');
        ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
        
        // Send the image to the backend (API call)
        const formData = new FormData();
        formData.append('image', img);

        try {
            const response = await fetch('/api/detect', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            drawDetectionResults(result, ctx);
        } catch (error) {
            console.error('Error detecting objects:', error);
        }
    };

    const drawDetectionResults = (result, ctx) => {
        if (!result || !result.detections) {
            alert('No detections found.');
            return;
        }
        
        // Set canvas size to image size
        detectionCanvas.width = result.imageWidth;
        detectionCanvas.height = result.imageHeight;

        result.detections.forEach(detection => {
            const { x, y, width, height, label, confidence } = detection;
            // Draw bounding box
            ctx.beginPath();
            ctx.rect(x, y, width, height);
            ctx.lineWidth = 3;
            ctx.strokeStyle = 'red';
            ctx.stroke();
            
            // Display label and confidence
            const text = `${label} (${(confidence * 100).toFixed(2)}%)`;
            ctx.font = '16px Arial';
            ctx.fillStyle = 'red';
            ctx.fillText(text, x, y - 10);

            // Add to result list
            const listItem = document.createElement('li');
            listItem.textContent = text;
            detectionsList.appendChild(listItem);
        });
    };
});
