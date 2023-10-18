document.addEventListener('DOMContentLoaded', () => {
    const captureButton= document.getElementById('capture-button');
    const optionsSection = document.getElementById('options');
    const takePhotoButton = document.getElementById('take-photo-button');
    const uploadPhotoButton = document.getElementById('upload-photo-button');
    const cameraContainer = document.getElementById('camera-container');
    const buttons = document.getElementById('buttons');
    const retakeButton = document.getElementById('retake-button');
    const nextButton = document.getElementById('next-button');
    const capturedPhoto = document.getElementById('captured-photo');
    const fileInput = document.getElementById('file-input');
    const canvas = capturedPhoto.getContext('2d');
    
    let isCaptured = false;
    const video = document.getElementById('camera-feed');

    function showOptions() {
        optionsSection.style.display = 'block';
        cameraContainer.style.display = 'none';
        buttons.style.display = 'none';
    }

    function showCamera() {
        optionsSection.style.display = 'none';
        cameraContainer.style.display = 'block';
        buttons.style.display = 'block';
    }

function takePhoto() {
    navigator.mediaDevices
        .getUserMedia({ video: { facingMode: 'environment' } })
        .then((stream) => {
            video.srcObject = stream;
        })
        .catch((error) => {
            console.error('Error accessing camera:', error);
        });
}

takePhotoButton.addEventListener('click', () => {
    takePhoto();
    showCamera();
});

captureButton.addEventListener('click', () => {
    if (!isCaptured) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
        capturedPhoto.style.display = 'block';
        video.style.display = 'none';

        captureButton.style.display = 'none';
        retakeButton.style.display = 'inline-block';
        nextButton.style.display = 'inline-block';

        isCaptured = true;
    }
});

retakeButton.addEventListener('click', () => {
    capturedPhoto.style.display = 'none';
    video.style.display = 'block';
    captureButton.style.display = 'inline-block';
    retakeButton.style.display = 'none';
    nextButton.style.display = 'none';

    isCaptured = false;
  });

  function sendImageToServer(imageData) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/create', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    console.log('Image uploaded but no redirect provided.');
                }
            } else {
                console.error('Image upload failed.');
            }
        }
    };    
    const data = JSON.stringify({ image: imageData });
    xhr.send(data);
}

nextButton.addEventListener('click', () => {
    if (isCaptured) {
        const imageBase64 = capturedPhoto.toDataURL('image/jpeg');
        sendImageToServer(imageBase64);
    }
});

uploadPhotoButton.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
        const reader = new FileReader();
        reader.onload = function () {
            const imageBase64 = reader.result;
            sendImageToServer(imageBase64);
        };
        reader.readAsDataURL(selectedFile);
    }
});

    showOptions();
});