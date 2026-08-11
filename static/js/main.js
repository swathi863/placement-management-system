/* ==========================================================================
   Placement Management System - Interactive Client Scripts
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Alert dismissals
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

  // Modal Dialog handling
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

  // File Upload Preview / Name Display
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const fileNameSpan = input.parentElement.querySelector('.file-name-display');
      if (fileNameSpan && input.files.length > 0) {
        fileNameSpan.textContent = `Selected: ${input.files[0].name}`;
      }
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
