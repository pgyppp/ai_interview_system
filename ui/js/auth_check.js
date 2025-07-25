document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const expiration = localStorage.getItem('expiration');

    if (!token || !expiration || Date.now() > parseInt(expiration)) {
        // Token is missing or expired, redirect to login page
        window.location.href = '/ui/index.html';
    }
});