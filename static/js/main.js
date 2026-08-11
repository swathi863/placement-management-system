/* ==========================================================================
   Placement Management System - Enhanced Interactive Client Scripts
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Alert dismissals with fade-out
  const alertCloses = document.querySelectorAll('.alert-close');
  alertCloses.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // Modal Dialog backdrop click handling
  const modalOverlays = document.querySelectorAll('.modal-overlay');
  modalOverlays.forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  const modalCloseBtns = document.querySelectorAll('.modal-close, [data-modal-close]');
  modalCloseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = btn.closest('.modal-overlay');
      if (overlay) {
        closeModal(overlay);
      }
    });
  });

  // File Upload Preview & Display
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const fileNameSpan = input.parentElement.querySelector('.file-name-display');
      if (fileNameSpan && input.files.length > 0) {
        fileNameSpan.textContent = `Selected: ${input.files[0].name}`;
      }
    });
  });

  // Attach Instant Live Search to input fields with data-table-target
  const liveSearchInputs = document.querySelectorAll('input[data-table-target]');
  liveSearchInputs.forEach(input => {
    input.addEventListener('keyup', () => {
      const tableId = input.getAttribute('data-table-target');
      filterTableRows(input.value, tableId);
    });
  });
});

// Helper Functions for Modals
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalElement) {
  if (typeof modalElement === 'string') {
    modalElement = document.getElementById(modalElement);
  }
  if (modalElement) {
    modalElement.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// In-Browser PDF Resume Preview Modal
function openPdfPreviewModal(pdfUrl, title) {
  let modal = document.getElementById('pdfPreviewModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'pdfPreviewModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-card" style="max-width: 850px; width: 95%; height: 85vh; display: flex; flex-direction: column;">
        <div class="modal-header">
          <h2 style="font-size: 1.2rem; font-weight: 700;" id="pdfModalTitle">Resume Preview</h2>
          <button type="button" class="modal-close" onclick="closeModal('pdfPreviewModal')">&times;</button>
        </div>
        <div style="flex: 1; overflow: hidden; background-color: var(--bg-subtle); border-radius: var(--radius-md);">
          <iframe id="pdfFrame" src="" style="width: 100%; height: 100%; border: none;"></iframe>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
          <a id="pdfDownloadLink" href="" target="_blank" class="btn btn-secondary btn-sm">Direct Download</a>
          <button type="button" class="btn btn-primary btn-sm" onclick="closeModal('pdfPreviewModal')">Close</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(modal);
    });
  }

  document.getElementById('pdfModalTitle').textContent = `Resume Preview - ${title || 'Candidate'}`;
  document.getElementById('pdfFrame').src = pdfUrl;
  document.getElementById('pdfDownloadLink').href = pdfUrl;
  openModal('pdfPreviewModal');
}

// Quick Helper for Status Modal Pre-filling (Admin Applications Page)
function openStatusModal(appId, studentName, jobTitle, currentStatus, currentRemarks) {
  const form = document.getElementById('statusModalForm');
  if (form) {
    form.action = `/admin/application/${appId}/status`;
    document.getElementById('modalStudentName').textContent = studentName;
    document.getElementById('modalJobTitle').textContent = jobTitle;
    document.getElementById('modalStatusSelect').value = currentStatus;
    document.getElementById('modalRemarksInput').value = currentRemarks || '';
    openModal('statusModal');
  }
}

// Quick Helper for Schedule Interview Modal (Admin Page)
function openScheduleModal(appId, studentName, jobTitle) {
  const form = document.getElementById('scheduleModalForm');
  if (form) {
    form.action = `/admin/interview/schedule/${appId}`;
    document.getElementById('schedStudentName').textContent = studentName;
    document.getElementById('schedJobTitle').textContent = jobTitle;
    openModal('scheduleModal');
  }
}

// Client-side Instant Table Row Filtering
function filterTableRows(query, tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const rows = table.querySelectorAll('tbody tr');
  const term = query.toLowerCase().trim();

  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    if (text.includes(term)) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}

// Export Table Data to CSV
function exportTableToCSV(tableId, filename = 'export.csv') {
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = Array.from(table.querySelectorAll('tr'));
  const csvContent = rows.map(row => {
    const cols = Array.from(row.querySelectorAll('th, td'));
    return cols.map(col => `"${col.innerText.replace(/"/g, '""').trim()}"`).join(',');
  }).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
