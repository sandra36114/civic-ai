async function submitComplaint(event) {
    event.preventDefault();

    const description = document.getElementById("description").value;
    const location = document.getElementById("location").value;

    // Temporary user ID
    // Later we will get this automatically from login/session
    const userId = localStorage.getItem("user_id");

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
                location: location
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