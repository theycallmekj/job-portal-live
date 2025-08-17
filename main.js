// Function to fetch and inject HTML content
const includeHTML = async (elementId, filePath) => {
    try {
        // This simple path works if the file structure is correct.
        const response = await fetch(filePath);
        if (!response.ok) {
            throw new Error(`Could not load ${filePath}: ${response.statusText}`);
        }
        const text = await response.text();
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = text;
        }
    } catch (error) {
        console.error(error);
    }
};

// This function runs after the header and footer are loaded
const initializePage = () => {
    // Mobile Menu Toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button-placeholder');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
        mobileMenuButton.id = 'mobile-menu-button';
    }

    // Dynamic Copyright Year
    const copyrightEl = document.getElementById('copyright-placeholder');
    if (copyrightEl) {
        const currentYear = new Date().getFullYear();
        copyrightEl.textContent = `© ${currentYear} AapkaRojgar.com. All Rights Reserved.`;
        copyrightEl.id = 'copyright';
    }

    // Highlight the active navigation link
    const currentUrl = window.location.href;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.href === currentUrl) {
            link.classList.add('active');
        }
    });
};

// Load header and footer, then initialize the page scripts
document.addEventListener('DOMContentLoaded', async () => {
    await includeHTML('header-placeholder', '_header.html');
    await includeHTML('footer-placeholder', '_footer.html');
    initializePage();
});
