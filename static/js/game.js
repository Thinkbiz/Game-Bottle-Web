document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Get initial stats from JSON data attribute
    const statsElement = document.getElementById('gameStats');
    const initialStats = JSON.parse(statsElement.dataset.initialStats);
    
    // Validate numeric values
    function validateNumber(value) {
        const num = parseInt(value, 10);
        return !isNaN(num) && num >= 0;
    }
    
    // Track page view with validated context
    function trackGameEvent(eventName, params) {
        // Validate and convert parameters
        const validatedParams = {
            health: validateNumber(params.health) ? parseInt(params.health, 10) : 0,
            score: validateNumber(params.score) ? parseInt(params.score, 10) : 0,
            xp: validateNumber(params.xp) ? parseInt(params.xp, 10) : 0
        };
        
        // Add CSRF token to request
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        };
        
        fetch('/api/track', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                event: eventName,
                params: validatedParams
            })
        }).catch(error => console.error('Event tracking error:', error));
    }
    
    // Initialize with validated stats
    trackGameEvent('screen_view', initialStats);
    
    // Track button clicks with validation
    document.addEventListener('click', function(event) {
        const button = event.target.closest('button[name="choice"]');
        if (!button) return;
        
        const choice = button.value;
        const validChoices = ['fight', 'run', 'search_alone', 'get_help', 'ignore', 'rest', 'adventure'];
        
        if (!validChoices.includes(choice)) {
            console.error('Invalid choice detected:', choice);
            return;
        }
        
        // Get current stats from DOM
        const stats = {
            health: document.querySelector('[data-stat="health"]').textContent,
            score: document.querySelector('[data-stat="score"]').textContent,
            xp: document.querySelector('[data-stat="xp"]').textContent
        };
        
        let eventType = 'game_action';
        if (['fight', 'run'].includes(choice)) {
            eventType = 'combat_choice';
        } else if (['search_alone', 'get_help', 'ignore'].includes(choice)) {
            eventType = 'treasure_choice';
        } else if (choice === 'rest') {
            eventType = 'rest_choice';
        } else if (choice === 'adventure') {
            eventType = 'adventure_choice';
        }
        
        trackGameEvent(eventType, stats);
    });

    // Track game over and victory events
    const eventType = document.body.dataset.eventType;
    const victoryType = document.body.dataset.victoryType;
    
    if (eventType === 'gameover') {
        trackGameEvent('game_over', initialStats);
    } else if (victoryType) {
        trackGameEvent('victory', {
            ...initialStats,
            victory_type: victoryType
        });
    }

    // Add animation for game images
    function showGameImages() {
        const images = document.querySelectorAll('.game-image');
        images.forEach(img => {
            // Wait for image to load
            if (img.complete) {
                setTimeout(() => img.classList.add('show'), 100);
            } else {
                img.onload = () => setTimeout(() => img.classList.add('show'), 100);
            }
        });
    }

    // Run image animations
    showGameImages();

    function updateProgressBars() {
        const bars = document.querySelectorAll('.progress-bar');
        
        bars.forEach(bar => {
            const currentValue = parseFloat(bar.getAttribute('data-value'));
            const previousValue = parseFloat(bar.getAttribute('data-previous'));
            
            if (currentValue !== previousValue) {
                // Remove existing classes first
                bar.classList.remove('increase', 'decrease');
                
                // Force a reflow
                void bar.offsetWidth;
                
                // Add appropriate class based on value change
                if (currentValue > previousValue) {
                    bar.classList.add('increase');
                } else if (currentValue < previousValue) {
                    bar.classList.add('decrease');
                }
                
                // Schedule removal of animation classes
                setTimeout(() => {
                    bar.classList.remove('increase', 'decrease');
                }, 1000);
            }
        });
    }

    // Run animation check immediately after page load
    updateProgressBars();
    
    // Also run when the page content updates
    const observer = new MutationObserver(updateProgressBars);
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });

    // Function to update progress bar widths
    function updateProgressWidth(bar, value, max) {
        // Remove all width classes
        bar.classList.forEach(className => {
            if (className.startsWith('health-width-')) {
                bar.classList.remove(className);
            }
        });
        
        // Calculate percentage and round to nearest 10
        const percentage = Math.round((value / max) * 10) * 10;
        bar.classList.add(`health-width-${percentage}`);
    }
}); 