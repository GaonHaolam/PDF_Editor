document.addEventListener('DOMContentLoaded', function () {

    const container = document.getElementById('pdfViewerContainer');
    if (!container) return;

    // Read config from data attributes
    const pdfUrl = container.dataset.pdfUrl;
    const filename = container.dataset.filename;
    const folderType = container.dataset.folderType;

    if (pdfUrl) {
        // --- PDF Viewer Logic ---
        const canvas = document.getElementById('pdfCanvas');
        const ctx = canvas.getContext('2d');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageNumSpan = document.getElementById('pageNum');
        const pageCountSpan = document.getElementById('pageCount');
        const zoomInBtn = document.getElementById('zoomIn');
        const zoomOutBtn = document.getElementById('zoomOut');
        const zoomLevelSpan = document.getElementById('zoomLevel');

        const deletePageBtn = document.getElementById('deletePageBtn');
        const deleteConfirmPopup = document.getElementById('deleteConfirmPopup');
        const confirmDeleteYes = document.getElementById('confirmDeleteYes');
        const confirmDeleteNo = document.getElementById('confirmDeleteNo');
        const saveBtn = document.getElementById('saveBtn');

        let pdfDoc = null;
        let pageNum = 1;
        let pageRendering = false;
        let pageNumPending = null;
        let scale = 1.0;

        /**
         * Get page info from document, resize canvas accordingly, and render page.
         * @param num Page number.
         */
        function renderPage(num) {
            pageRendering = true;

            // Fetch page
            pdfDoc.getPage(num).then(function (page) {
                const viewport = page.getViewport({ scale: scale });
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // Render PDF page into canvas context
                const renderContext = {
                    canvasContext: ctx,
                    viewport: viewport
                };
                const renderTask = page.render(renderContext);

                // Wait for render to finish
                renderTask.promise.then(function () {
                    pageRendering = false;
                    if (pageNumPending !== null) {
                        renderPage(pageNumPending);
                        pageNumPending = null;
                    }
                });
            });

            // Update page counters
            if (pageNumSpan) pageNumSpan.textContent = num;

            // Update button states
            if (prevBtn) prevBtn.disabled = num <= 1;
            if (nextBtn) nextBtn.disabled = num >= pdfDoc.numPages;

            // Hide popup when changing pages
            if (deleteConfirmPopup) deleteConfirmPopup.classList.add('d-none');
        }

        /**
         * If another page rendering in progress, waits until the rendering is
         * finised. Otherwise, executes rendering immediately.
         */
        function queueRenderPage(num) {
            if (pageRendering) {
                pageNumPending = num;
            } else {
                renderPage(num);
            }
        }

        /**
         * Asynchronously downloads PDF.
         */
        function loadPDF(url) {
            pdfjsLib.getDocument(url).promise.then(function (pdfDoc_) {
                pdfDoc = pdfDoc_;
                if (pageCountSpan) pageCountSpan.textContent = pdfDoc.numPages;

                // Adjust pageNum if it's out of bounds (e.g. deleted last page)
                if (pageNum > pdfDoc.numPages) {
                    pageNum = pdfDoc.numPages;
                }
                if (pageNum < 1) pageNum = 1;

                renderPage(pageNum);
            }).catch(err => {
                console.error('Error loading PDF:', err);
                // Handle error (e.g., show alert)
            });
        }

        // Initial Load
        loadPDF(pdfUrl);

        // Event Listeners
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (pageNum <= 1) return;
                pageNum--;
                queueRenderPage(pageNum);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (pageNum >= pdfDoc.numPages) return;
                pageNum++;
                queueRenderPage(pageNum);
            });
        }

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => {
                scale += 0.2;
                if (zoomLevelSpan) zoomLevelSpan.textContent = Math.round(scale * 100) + '%';
                queueRenderPage(pageNum);
            });
        }

        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => {
                if (scale <= 0.4) return;
                scale -= 0.2;
                if (zoomLevelSpan) zoomLevelSpan.textContent = Math.round(scale * 100) + '%';
                queueRenderPage(pageNum);
            });
        }

        // Delete Page Logic
        if (deletePageBtn && deleteConfirmPopup) {

            // Show Popup
            deletePageBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent closing immediately if we add outside click listener
                // Toggle visibility
                if (deleteConfirmPopup.classList.contains('d-none')) {
                    deleteConfirmPopup.classList.remove('d-none');
                } else {
                    deleteConfirmPopup.classList.add('d-none');
                }
            });

            // Hide on No
            if (confirmDeleteNo) {
                confirmDeleteNo.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteConfirmPopup.classList.add('d-none');
                });
            }

            // Execute on Yes
            if (confirmDeleteYes) {
                confirmDeleteYes.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    deleteConfirmPopup.classList.add('d-none'); // Hide immediately

                    try {
                        const response = await fetch('/delete_page', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                filename: filename,
                                page_number: pageNum,
                                folder_type: folderType
                            })
                        });

                        const data = await response.json();

                        if (data.success) {
                            // Reload PDF without page refresh
                            // Add timestamp to prevent caching
                            const timestamp = new Date().getTime();
                            const separator = pdfUrl.includes('?') ? '&' : '?';
                            const newUrl = `${pdfUrl}${separator}t=${timestamp}`;
                            loadPDF(newUrl);
                        } else {
                            alert('Error deleting page: ' + (data.error || 'Unknown error'));
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('Failed to send delete request.');
                    }
                });
            }

            // Save File Logic
            if (saveBtn) {
                saveBtn.addEventListener('click', async function () {
                    const btn = this;
                    const originalContent = btn.innerHTML;

                    try {
                        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
                        btn.disabled = true;

                        const response = await fetch('/save_file', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ filename: filename, folder_type: folderType })
                        });
                        const data = await response.json();

                        if (data.success) {
                            btn.innerHTML = '<i class="bi bi-check-lg me-2"></i>Saved!';
                            btn.classList.remove('btn-success');
                            btn.classList.add('btn-outline-success');

                            setTimeout(() => {
                                btn.innerHTML = originalContent;
                                btn.disabled = false;
                                btn.classList.add('btn-success');
                                btn.classList.remove('btn-outline-success');
                            }, 2000);
                        } else {
                            alert('Error saving file: ' + (data.error || 'Unknown error'));
                            btn.innerHTML = originalContent;
                            btn.disabled = false;
                        }
                    } catch (e) {
                        console.error(e);
                        alert('Failed to save file.');
                        btn.innerHTML = originalContent;
                        btn.disabled = false;
                    }
                });
            }

            // Close popup when clicking outside
            document.addEventListener('click', function (event) {
                if (!deletePageBtn.contains(event.target) && !deleteConfirmPopup.contains(event.target)) {
                    deleteConfirmPopup.classList.add('d-none');
                }
            });
        }
    }
});
