// Function to fetch and inject HTML content
const includeHTML = async (elementId, filePath) => {
    try {
        // With the <base> tag, a simple relative path now works perfectly everywhere.
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
    // --- Mobile Menu Toggle ---
    const mobileMenuButton = document.getElementById('mobile-menu-button-placeholder');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
        mobileMenuButton.id = 'mobile-menu-button';
    }

    // --- Dynamic Copyright Year ---
    const copyrightEl = document.getElementById('copyright-placeholder');
    if (copyrightEl) {
        const currentYear = new Date().getFullYear();
        copyrightEl.textContent = `© ${currentYear} AapkaRojgar.com. All Rights Reserved.`;
        copyrightEl.id = 'copyright';
    }

    // --- Highlight the active navigation link ---
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
             link.classList.add('active');
        }
    });
     // Special case for home page
    if (currentPath.endsWith('/') || currentPath.endsWith('/index.html')) {
        document.querySelector('a[href="index.html"]')?.classList.add('active');
    }
};

// Load header and footer, then initialize the page scripts
document.addEventListener('DOMContentLoaded', async () => {
    // Now these simple paths will be correctly interpreted by the browser
    await includeHTML('header-placeholder', '_header.html');
    await includeHTML('footer-placeholder', '_footer.html');
    initializePage();
});
