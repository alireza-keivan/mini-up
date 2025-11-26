document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(d => {
        d.addEventListener('click', e => {
            e.stopPropagation();
            d.querySelector('.dropdown-content').classList.toggle('show');
        });
    });
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-content').forEach(c => c.classList.remove('show'));
    });
});
