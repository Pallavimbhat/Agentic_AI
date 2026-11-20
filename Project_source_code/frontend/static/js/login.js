const loginForm = document.getElementById("login-form");
const loginButton = document.getElementById("login-button");
const errorBox = document.getElementById("login-error");

function showError(message) {
    errorBox.textContent = message;
}

function redirectByRole(role) {
    if (role === "professor") {
        window.location.href = "/professor";
    } else if (role === "student") {
        window.location.href = "/student";
    } else {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
        showError("This account has an unsupported role. Please contact the administrator.");
    }
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showError("");

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    loginButton.disabled = true;
    loginButton.querySelector(".button-text").textContent = "Signing in...";

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to sign in. Check your details and try again.");
        }

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("current_user", JSON.stringify(data.user));
        redirectByRole(data.user.role);
    } catch (error) {
        showError(error.message || "Something went wrong. Please try again.");
        loginButton.disabled = false;
        loginButton.querySelector(".button-text").textContent = "Sign in";
    }
});

// If a valid session already exists, take the user to their role-based area.
(async function checkExistingSession() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const response = await fetch("/auth/me", {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("Session expired");

        const data = await response.json();
        localStorage.setItem("current_user", JSON.stringify(data.user));
        redirectByRole(data.user.role);
    } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
    }
})();
