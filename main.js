// --- NEW: A smarter function to build the correct path ---
// This will work on both your local PC and the live GitHub Pages site.
const getBasePath = () => {
    const path = window.location.pathname;
    // On GitHub Pages, the path is /repository-name/page.html
    // We want to get the /repository-name/ part.
    if (path.split('/')[1]) {
        const repoName = path.split('/')[1];
        // Check if we are on the local server or a live server
        if (window.location.hostname.includes('github.io')) {
             return `/${repoName}/`;
        }
    }
    // For local testing (file:// or localhost), the base path is just root.
    return '/';
};

// Function to fetch and inject HTML content
const includeHTML = async (elementId, relativePath) => {
    // --- MODIFIED: Use the base path to create a full, absolute path ---
    const basePath = getBasePath();
    // Prevent double slashes if the path starts with one
    const cleanRelativePath = relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
    const filePath = `${basePath}${cleanRelativePath}`;

    try {
        // Use the new, correct filePath for fetching
        const response = await fetch(filePath);
        if (!response.ok) {
            // Throw a more informative error
            throw new Error(`Could not load ${filePath}: ${response.status} ${response.statusText}`);
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
    // This logic needs to be aware of the base path as well
    const basePath = getBasePath();
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        // Construct the full expected path for comparison
        const linkPath = new URL(link.href).pathname;
        const linkCategory = new URL(link.href).searchParams.get('category');
        const currentCategory = new URL(window.location.href).searchParams.get('category');
        
        // Handle index.html - check if the current path ends with the base path or index.html
        if (currentPath === basePath || currentPath === `${basePath}index.html`) {
            if(link.textContent === 'Home') {
                 link.classList.add('active');
            }
        }
        // Handle other pages
        else if (linkPath === currentPath && linkCategory === currentCategory) {
            link.classList.add('active');
        }
    });
};

// Load header and footer, then initialize the page scripts
document.addEventListener('DOMContentLoaded', async () => {
    // --- NO CHANGE HERE ---
    // The relative paths are still correct, the includeHTML function now handles the complexity
    await includeHTML('header-placeholder', '_header.html');
    await includeHTML('footer-placeholder', '_footer.html');
    initializePage();
});
