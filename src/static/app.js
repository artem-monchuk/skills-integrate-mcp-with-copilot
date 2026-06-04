document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const attendanceActivitySelect = document.getElementById("attendance-activity");
  const signupForm = document.getElementById("signup-form");
  const attendanceEmailInput = document.getElementById("attendance-email");
  const attendanceTokenInput = document.getElementById("attendance-token");
  const checkinButton = document.getElementById("checkin-button");
  const checkoutButton = document.getElementById("checkout-button");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and selects
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
      attendanceActivitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        const attendanceHTML =
          details.attendance && details.attendance.length > 0
            ? `<div class="attendance-section">
                <h5>Attendance history:</h5>
                <ul class="attendance-list">
                  ${details.attendance
                    .map(
                      (entry) =>
                        `<li><strong>${entry.email}</strong> ${entry.action === "checkin" ? "checked in" : "checked out"} at ${new Date(
                          entry.timestamp
                        ).toLocaleString()}</li>`
                    )
                    .join("")}
                </ul>
              </div>`
            : `<p><em>No attendance recorded yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <p><strong>QR Token:</strong> <code>${details.qr_token}</code></p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
          <div class="attendance-records">
            ${attendanceHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
        attendanceActivitySelect.appendChild(option.cloneNode(true));
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle sign up
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  async function handleAttendance(action) {
    const email = attendanceEmailInput.value;
    const activity = attendanceActivitySelect.value;
    const token = attendanceTokenInput.value;

    if (!activity) {
      showMessage("Please select an activity for attendance.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/${action}?email=${encodeURIComponent(
          email
        )}&token=${encodeURIComponent(token)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        attendanceTokenInput.value = "";
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Attendance request failed. Please try again.", "error");
      console.error("Error submitting attendance:", error);
    }
  }

  checkinButton.addEventListener("click", () => handleAttendance("checkin"));
  checkoutButton.addEventListener("click", () => handleAttendance("checkout"));

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Initialize app
  fetchActivities();
});
