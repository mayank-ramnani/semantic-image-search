var sdk = apigClientFactory.newClient({});

async function searchPhotos() {
    const searchQuery = document.getElementById('searchInput').value;

    params = {'q': searchQuery};
    try {
        response = await sdk.searchGet(params, {});
        displayResults(response["data"]["photoUrls"]);
    }
    catch (err) {
        displayError(err);
    }
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';
    results.forEach(photo => {
        const img = document.createElement('img');
        img.src = photo;
        resultsContainer.appendChild(img);
    });
}

function displayError(err) {
    const resultsContainer = document.getElementById('results');
    console.log(err);
    resultsContainer.innerHTML = `<p> No Image Found </p>`;
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
    alert('File uploaded!');
}