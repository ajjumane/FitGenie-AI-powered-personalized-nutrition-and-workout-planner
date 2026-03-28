document.addEventListener('DOMContentLoaded', function () {
    // Loading overlay logic
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function () {
                if (this.action && (this.action.includes('logout') || this.classList.contains('no-loader'))) return;
                overlay.style.display = 'flex';
            });
        });
    }

    // Background Canvas Animation (Ultra-Smooth High-Perf)
    const canvas = document.getElementById('genie-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const icons = ['🥑','🏋️','💪','🔥','⚡','🏃','🥗','🥦','🍎','🥕','✨','🧘','🎯','💯'];
        const particles = [];
        let targetX = 0, targetY = 0;
        let mouseX = 0, mouseY = 0;
        let lastTime = 0;
        
        function resize() {
            const dpr = window.devicePixelRatio || 1;
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            ctx.scale(dpr, dpr);
            canvas.style.width = window.innerWidth + 'px';
            canvas.style.height = window.innerHeight + 'px';
        }
        
        resize();
        window.addEventListener('resize', resize);
        window.addEventListener('mousemove', (e) => {
            targetX = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
            targetY = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);
        });

        // Initialize particles
        for (let i = 0; i < 28; i++) {
            const z = 0.2 + Math.random() * 0.8;
            particles.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
                z: z,
                size: Math.floor(16 + z * 22),
                vx: (Math.random() - 0.5) * (0.2 + z * 0.25),
                vy: -0.15 - z * 0.35,
                icon: icons[Math.floor(Math.random() * icons.length)],
                alpha: 0.12 + z * 0.18,
                rot: Math.random() * Math.PI * 2,
                rotV: (Math.random() - 0.5) * 0.015,
                offset: Math.random() * 2000
            });
        }

        function animate(time) {
            const dt = time - lastTime;
            lastTime = time;
            
            ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
            
            // Ultra-Smooth LERP
            mouseX += (targetX - mouseX) * 0.04;
            mouseY += (targetY - mouseY) * 0.04;

            particles.forEach(p => {
                // Liquid drift physics
                const drift = Math.sin(time * 0.0007 + p.offset) * 0.25;
                
                // Parallax shift
                const sx = mouseX * p.z * 45;
                const sy = mouseY * p.z * 45;

                p.x += p.vx + drift;
                p.y += p.vy;
                p.rot += p.rotV;
                
                // Optimized screen-wrap
                if (p.y < -60) p.y = window.innerHeight + 60;
                if (p.x < -100) p.x = window.innerWidth + 100;
                if (p.x > window.innerWidth + 100) p.x = -100;
                
                ctx.save();
                ctx.globalAlpha = p.alpha;
                
                // Integer Snapping for Pixel-Perfect Rendering (Prevents flicker)
                const renderX = Math.floor(p.x + sx);
                const renderY = Math.floor(p.y + sy);
                
                ctx.translate(renderX, renderY);
                ctx.rotate(p.rot);
                
                ctx.font = p.size + 'px serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(p.icon, 0, 0);
                ctx.restore();
            });
            requestAnimationFrame(animate);
        }
        requestAnimationFrame(animate);
    }
});