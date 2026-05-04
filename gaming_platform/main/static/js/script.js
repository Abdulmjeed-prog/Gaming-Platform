document.addEventListener('DOMContentLoaded', function () {

    // search toggle
    const searchToggle = document.getElementById('search-toggle');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');

    if (searchToggle && searchForm) {
        searchToggle.addEventListener('click', function () {
            searchForm.classList.toggle('open');
            if (searchForm.classList.contains('open')) {
                searchInput.focus();
            }
        });

        document.addEventListener('click', function (e) {
            if (!searchForm.contains(e.target) && e.target !== searchToggle) {
                searchForm.classList.remove('open');
            }
        });
    }

    // user dropdown
    const userToggle = document.getElementById('user-menu-toggle');
    const userDropdown = document.getElementById('user-dropdown');

    if (userToggle && userDropdown) {
        userToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('open');
        });

        document.addEventListener('click', function () {
            userDropdown.classList.remove('open');
        });
    }

    // carousel auto-init
    const track = document.getElementById('carousel-track');
    if (track) {
        const count = track.querySelectorAll('.carousel-slide').length;
        initCarousel(count);
    }

});


function initCarousel(count) {
    if (count < 2) return;

    const track = document.getElementById('carousel-track');
    const dots = document.querySelectorAll('.carousel-dot');
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');

    let current = 0;
    let timer;

    function goTo(index) {
        current = (index + count) % count;
        track.style.transform = 'translateX(-' + (current * 100) + '%)';
        dots.forEach(function (d, i) {
            d.classList.toggle('carousel-dot--active', i === current);
        });
    }

    function startAuto() {
        timer = setInterval(function () { goTo(current + 1); }, 4000);
    }

    function resetAuto() {
        clearInterval(timer);
        startAuto();
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function () { goTo(current - 1); resetAuto(); });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function () { goTo(current + 1); resetAuto(); });
    }

    dots.forEach(function (dot, i) {
        dot.addEventListener('click', function () { goTo(i); resetAuto(); });
    });

    startAuto();
}

// card video hover
(function () {
    var hoverTimer;

    function initCardVideos() {
        document.querySelectorAll('.game-card').forEach(function (card) {
            var video = card.querySelector('.game-card-video');
            if (!video) return;

            card.addEventListener('mouseenter', function () {
                hoverTimer = setTimeout(function () {
                    if (!video.src) {
                        video.src = video.dataset.src;
                    }
                    video.play().then(function () {
                        video.classList.add('playing');
                    }).catch(function () {});
                }, 300);
            });

            card.addEventListener('mouseleave', function () {
                clearTimeout(hoverTimer);
                video.pause();
                video.classList.remove('playing');
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCardVideos);
    } else {
        initCardVideos();
    }
})();