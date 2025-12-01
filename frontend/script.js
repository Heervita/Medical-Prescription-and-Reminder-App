const BASE_URL = "http://127.0.0.1:8000";

// FIX 1 — Add navigation function
function goTo(page) {
    window.location.href = page;
}

// FIX 2 — Add logout function
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("name");
    window.location.href = "index.html";
}

// SIGNUP
async function signup() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch(`${BASE_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    });

    const data = await response.json();
    document.getElementById("message").innerText = data.message || "Signup complete!";

    // Save name locally so dashboard can show it
    localStorage.setItem("name", name);

    setTimeout(() => {
        window.location.href = "index.html";
    }, 800);
}


// LOGIN
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (data.token) {
        localStorage.setItem("token", data.token);
        window.location.href = "dashboard.html";
    } else {
        document.getElementById("message").innerText = "Wrong email or password!";
    }
}


async function addPrescription() {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Please login again.");
        window.location.href = "index.html";
        return;
    }

    const title = document.getElementById("title").value;
    const doctor_name = document.getElementById("doctor_name").value;
    const date = document.getElementById("date").value;

    const response = await fetch(`${BASE_URL}/prescriptions/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ title, doctor_name, date })
    });

    const data = await response.json();

    if (data.id) {
        document.getElementById("message").innerText = "Prescription added!";
        // Optionally save last prescription ID
        localStorage.setItem("last_prescription_id", data.id);
    } else {
        document.getElementById("message").innerText = data.detail || "Failed!";
    }
}

async function addMedicine() {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Please login again.");
        window.location.href = "index.html";
        return;
    }

    const prescription_id = document.getElementById("prescription_id").value;
    const name = document.getElementById("name").value;
    const dosage = document.getElementById("dosage").value;
    const frequency = parseInt(document.getElementById("frequency").value);
    const times = document.getElementById("times").value.split(",").map(t => t.trim());
    const start_date = document.getElementById("start_date").value;
    const end_date = document.getElementById("end_date").value;

    const response = await fetch(`${BASE_URL}/medicine/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            prescription_id,
            name,
            dosage,
            frequency,
            times,
            start_date,
            end_date
        })
    });

    const data = await response.json();

    if (data.id) {
        document.getElementById("message").innerText = "Medicine added!";
    } else {
        document.getElementById("message").innerText = data.detail || "Error adding medicine!";
    }
}

async function loadPrescriptions() {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Please login again.");
        window.location.href = "index.html";
        return;
    }

    const response = await fetch(`${BASE_URL}/prescriptions/`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    const table = document.getElementById("prescriptionTable");

    data.forEach(p => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${p.title}</td>
            <td>${p.doctor_name}</td>
            <td>${p.date}</td>
            <td>${p.medicines.length} medicines</td>
        `;

        table.appendChild(row);
    });
}

async function loadMedicines() {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Please login again.");
        window.location.href = "index.html";
        return;
    }

    const response = await fetch(`${BASE_URL}/medicine/all`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    const table = document.getElementById("medicineTable");

    data.forEach(m => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${m.name}</td>
            <td>${m.dosage}</td>
            <td>${m.frequency} times/day</td>
            <td>${m.times.join(", ")}</td>
            <td>${m.start_date}</td>
            <td>${m.end_date}</td>
            <td>${m.prescription_id}</td>
        `;

        table.appendChild(row);
    });
}
