// Shared utilites for File Upload and Action Selection

/**
 * Initializes drag and drop functionality for a drop zone.
 * @param {HTMLElement} dropZone - The element that accepts drops.
 * @param {HTMLElement} fileInput - The hidden file input.
 * @param {HTMLElement} fileDisplay - Element to show selected filename.
 * @param {HTMLElement} fileName - Element to update with filename.
 * @param {Function} callback - Function called when file is selected.
 */
function setupDragAndDrop(dropZone, fileInput, fileDisplay, fileName, callback) {
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('bg-white', 'shadow-lg', 'border-primary');
        dropZone.classList.remove('bg-light');
    });

    ['dragleave', 'dragend', 'drop'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('bg-white', 'shadow-lg', 'border-primary');
            dropZone.classList.add('bg-light');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0], fileInput, fileDisplay, fileName, callback);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFileSelect(fileInput.files[0], fileInput, fileDisplay, fileName, callback);
        }
    });
}

function handleFileSelect(file, fileInput, fileDisplay, fileName, callback) {
    // Update input files property manually if drag dropped
    if (fileInput.files[0] !== file) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
    }

    if (fileName) fileName.textContent = file.name;
    if (fileDisplay) fileDisplay.classList.remove('d-none');

    if (callback) callback(file);
}

/**
 * Initializes selection logic for action cards.
 * @param {NodeList} actionCards - List of card elements.
 * @param {HTMLInputElement} hiddenInput - The input to store selected value.
 * @param {Function} callback - Function called when selection changes.
 */
function setupActionCards(actionCards, hiddenInput, callback) {
    if (!actionCards || actionCards.length === 0) return;

    const selectedClass = 'border-primary';
    const selectedBgClass = 'bg-primary';
    const selectedBgOpacity = 'bg-opacity-10';

    actionCards.forEach(card => {
        card.addEventListener('click', () => {
            // Deselect all
            actionCards.forEach(c => {
                c.classList.remove('border', 'border-2', selectedClass, selectedBgClass, selectedBgOpacity);
                c.classList.add('border-0');
            });

            // Select clicked
            card.classList.remove('border-0');
            card.classList.add('border', 'border-2', selectedClass, selectedBgClass, selectedBgOpacity);

            // Update Input
            const val = card.getAttribute('data-value');
            if (hiddenInput) hiddenInput.value = val;

            if (callback) callback(val);
        });
    });
}

/**
 * @param {string} submitBtnId - The ID of the submit button.
 * @param {string} actionInputId - The ID of the hidden input for the action value.
 */
function initializeUploadPage(submitBtnId, actionInputId) {
    document.addEventListener('DOMContentLoaded', function () {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileDisplay = document.getElementById('fileDisplay');
        const fileName = document.getElementById('fileName');
        const actionInput = document.getElementById(actionInputId);
        const submitButton = document.getElementById(submitBtnId);
        const actionCards = document.querySelectorAll('.action-card');

        let fileSelected = false;
        let actionSelected = false;

        function updateSubmitButton() {
            if (submitButton) {
                submitButton.disabled = !(fileSelected && actionSelected);
            }
        }

        setupDragAndDrop(dropZone, fileInput, fileDisplay, fileName, (file) => {
            fileSelected = true;
            updateSubmitButton();
        });

        setupActionCards(actionCards, actionInput, (val) => {
            actionSelected = true;
            updateSubmitButton();
        });
    });
}
