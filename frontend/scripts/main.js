var sdk = apigClientFactory.newClient({});

async function searchPhotos() {
    const searchQuery = document.getElementById('searchInput').value;

    params = {'q': searchQuery};
    
    return sdk.searchGet(params, {});

    // const response = await fetch(`/v1/search?q=${}`);
    // const data = await response.json();
    // displayResults(data.results);
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';
    results.forEach(photo => {
        const img = document.createElement('img');
        img.src = photo.url;
        resultsContainer.appendChild(img);

        const labels = document.createElement('p');
        labels.textContent = `Labels: ${photo.labels.join(', ')}`;
        resultsContainer.appendChild(labels);
    });
}

async function uploadPhoto() {
    const fileInput = document.getElementById('photoInput');
    const customLabelsInput = document.getElementById('customLabelsInput');
    const file = fileInput.files[0];
    console.log(file);

    const customLabels = customLabelsInput.value.split(',').map(label => label.trim());

    url = "https://v7zkpaz31g.execute-api.us-east-1.amazonaws.com/prod/upload/" + file.name

    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', "image/jpg")
    xhr.setRequestHeader("x-amz-meta-customLabels", [customLabels])
    // Send the binary data.
    // Since a File is a Blob, you can send it directly.
    xhr.send(file);
    return;
    // if (response.ok) {
    //     alert('Photo uploaded successfully!');
    // } else {
    //     alert('Failed to upload photo.');
    // }
}