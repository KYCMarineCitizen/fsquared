// Navigation and small UI helpers for Fsquared

document.addEventListener('DOMContentLoaded', function () {
	// set footer year
	const yearEl = document.getElementById('year');
	if (yearEl) yearEl.textContent = new Date().getFullYear();

	// Mobile nav toggle
	const navToggle = document.getElementById('nav-toggle');
	const primaryNav = document.getElementById('primary-nav');
	if (navToggle && primaryNav) {
		navToggle.addEventListener('click', function () {
			const expanded = this.getAttribute('aria-expanded') === 'true';
			this.setAttribute('aria-expanded', String(!expanded));
			primaryNav.classList.toggle('open');
		});
	}

	// Dropdowns
	document.querySelectorAll('.dropdown').forEach(function (dd) {
		const btn = dd.querySelector('.dropdown-toggle');
		if (!btn) return;
		btn.addEventListener('click', function (e) {
			const expanded = this.getAttribute('aria-expanded') === 'true';
			this.setAttribute('aria-expanded', String(!expanded));
			dd.classList.toggle('open');
			e.stopPropagation();
		});
	});

	// Close dropdowns / nav when clicking outside
	document.addEventListener('click', function (e) {
		// close dropdowns
		document.querySelectorAll('.dropdown.open').forEach(function (openDd) {
			openDd.classList.remove('open');
			const btn = openDd.querySelector('.dropdown-toggle');
			if (btn) btn.setAttribute('aria-expanded', 'false');
		});
		// close mobile nav
		if (primaryNav && primaryNav.classList.contains('open')) {
			primaryNav.classList.remove('open');
			if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
		}
	});

	// Prevent closing when clicking inside dropdown
	document.querySelectorAll('.dropdown-menu').forEach(function (menu) {
		menu.addEventListener('click', function (e) {
			e.stopPropagation();
		});
	});
  
		// Quick contact form posts to FastAPI relay
		const quickForm = document.getElementById('quick-contact-form');
		if (quickForm) {
			const statusEl = document.getElementById('quick-contact-status');
			const submitBtn = quickForm.querySelector('button[type="submit"]');
			const endpoint = quickForm.dataset.endpoint || '/contact';

			const setStatus = (message, tone) => {
				if (!statusEl) return;
				statusEl.textContent = message;
				statusEl.className = `form-status ${tone || ''}`.trim();
			};

			quickForm.addEventListener('submit', async function (e) {
				e.preventDefault();
				if (!submitBtn) return;

				const companyField = quickForm.querySelector('#company');
				const nameField = quickForm.querySelector('#name');
				const emailField = quickForm.querySelector('#email');
				const messageField = quickForm.querySelector('#message');

				if (!nameField || !emailField || !messageField) {
					setStatus('Form is missing required fields. Please reload the page and try again.', 'error');
					return;
				}

				const companyLabel = companyField && companyField.selectedIndex >= 0
					? companyField.options[companyField.selectedIndex].text
					: 'General';
				const name = nameField.value.trim();
				const fromEmail = emailField.value.trim();
				const message = messageField.value.trim();

				if (!name || !fromEmail || !message) {
					setStatus('Please complete all fields before submitting.', 'error');
					return;
				}

				setStatus('Sending your message…', 'pending');
				submitBtn.disabled = true;

				try {
					const response = await fetch(endpoint, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({
							name,
							email: fromEmail,
							message,
							company: companyLabel,
						}),
					});

					let result = {};
					try {
						result = await response.json();
					} catch (_) {
						// ignore parse errors; handled below
					}

					if (!response.ok || result.error) {
						const errorMessage = result.error || 'We could not send your message just now. Please try again or email info@fsquared.ai.';
						throw new Error(errorMessage);
					}

					setStatus('Thanks! Your message has been sent.', 'success');
					quickForm.reset();
					quickForm.reset();
				} catch (err) {
					setStatus(err.message || 'We could not send your message just now. Please try again or email info@fsquared.ai.', 'error');
				} finally {
					submitBtn.disabled = false;
				}
			});
		}
});
