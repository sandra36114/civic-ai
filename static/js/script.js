// ===============================
// REGISTER
// ===============================

async function registerUser(event) {
    event.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.status === "success") {
            alert("Account created successfully!");
            window.location.href = "/";
        } else {
            alert(data.message);
        }

    } catch (error) {
        console.error(error);
        alert("Unable to connect to CivicAI server.");
    }
}


// ===============================
// LOGIN
// ===============================

async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.status === "success") {

            // Save logged-in user information
            localStorage.setItem("user_id", data.user.id);
            localStorage.setItem("user_name", data.user.name);
            localStorage.setItem("user_role", data.user.role);

            alert("Login successful!");

            // Send admin to admin dashboard
            if (data.user.role === "admin") {
                window.location.href = "/admin";
            } else {
                window.location.href = "/dashboard";
            }

        } else {
            alert(data.message);
        }

    } catch (error) {
        console.error(error);
        alert("Unable to connect to CivicAI server.");
    }
}


// ===============================
// SUBMIT COMPLAINT
// ===============================

async function submitComplaint(event) {
    event.preventDefault();

    const description =
        document.getElementById("description").value;

    const location =
        document.getElementById("location").value;

    const userId =
        localStorage.getItem("user_id") ||
        JSON.parse(localStorage.getItem("user") || "{}").id;

    if (!userId) {
        alert("Please login first.");
        window.location.href = "/login";
        return;
    }

    try {

        const response = await fetch("/api/complaints", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                user_id: userId,
                description: description,
                location: location,
                has_evidence: document.getElementById("evidence")?.files.length > 0
            })
        });

        const data = await response.json();

        if (data.status === "success") {

            alert("Complaint submitted successfully!");

            window.location.href =
                "/complaint-result/" + data.complaint_id;

        } else {

            alert(data.message);
        }

    } catch (error) {

        console.error(error);

        alert("Unable to connect to CivicAI server.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("form[data-login-form]");

    if (!loginForm) return;

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = document.querySelector("#email").value;
        const password = document.querySelector("#password").value;

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                alert("Login successful!");

                // Save user information for later pages
                localStorage.setItem("user", JSON.stringify(data.user));

                window.location.href = "/dashboard";
            } else {
                alert(data.message || "Login failed.");
            }

        } catch (error) {
            console.error(error);
            alert("Could not connect to the server.");
        }
    });
});

