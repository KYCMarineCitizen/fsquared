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
  
		// Quick contact form: open mail client addressed to selected company
		const quickForm = document.getElementById('quick-contact-form');
		if (quickForm) {
			quickForm.addEventListener('submit', function (e) {
				e.preventDefault();
				const form = e.target;
				const company = form.company.value;
				const name = form.name.value;
				const fromEmail = form.email.value;
				const message = form.message.value;

				// map company key to email address
						const map = {
							fsquared: 'kyc@fsquared.ai',
							onlyallow: 'kyc@onlyallow.ai',
							quirkbot: 'kyc@quirkbot.ai',
							virsfor: 'kyc@virsfor.ai',
							batchforge: 'kyc@batchforge.ai'
						};

				const to = map[company] || 'info@fsquared.ai';

				const subject = encodeURIComponent('Website inquiry from ' + name + ' (' + fromEmail + ')');
				const body = encodeURIComponent('Name: ' + name + '\nEmail: ' + fromEmail + '\n\nMessage:\n' + message);

				// open user's mail client
				window.location.href = `mailto:${to}?subject=${subject}&body=${body}`;
			});
		}
});
