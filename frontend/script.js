const BASE_URL = "http://127.0.0.1:8000";

function goTo(page) {
    window.location.href = page;
}

function logout() {
    localStorage.clear();
    goTo("index.html");
}

/* ---------------------- SIGNUP ---------------------- */
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

    if (data.message) {
        localStorage.setItem("name", name);
        goTo("index.html");
    }
}

/* ---------------------- LOGIN ---------------------- */
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const r = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await r.json();

    if (data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("name", data.name);
        goTo("dashboard.html");
    }
}

/* ----------------- ADD PRESCRIPTION ----------------- */
async function addPrescription() {
    const token = localStorage.getItem("token");

    const r = await fetch(`${BASE_URL}/prescriptions/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            title: document.getElementById("title").value,
            doctor_name: document.getElementById("doctor_name").value,
            date: document.getElementById("date").value
        })
    });

    const data = await r.json();
    alert("Saved!");
}

/* ----------------- TIME PICKER SYSTEM ----------------- */
function addTimePicker() {
    const container = document.getElementById("timeContainer");

    const div = document.createElement("div");
    div.className = "time-row";

    div.innerHTML = `
        <input type="time" class="input timeInput">
        <button class="remove-btn" onclick="this.parentElement.remove()">✖</button>
    `;

    container.appendChild(div);
}

/* ----------------- ADD MEDICINE ----------------- */
async function saveMed() {
    const token = localStorage.getItem("token");

    let times = [];
    document.querySelectorAll(".timeInput").forEach(t => {
        if (t.value) times.push(t.value);
    });

    const r = await fetch(`${BASE_URL}/medicine/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            prescription_id: document.getElementById("prescription_id").value,
            name: document.getElementById("name").value,
            dosage: document.getElementById("dosage").value,
            frequency: document.getElementById("frequency").value,
            times: times,
            start_date: document.getElementById("start_date").value,
            end_date: document.getElementById("end_date").value
        })
    });

    const data = await r.json();
    alert("Medicine Saved!");
}

/* ----------------- LOAD PRESCRIPTIONS ----------------- */
async function loadPrescriptions() {
    const token = localStorage.getItem("token");

    const r = await fetch(`${BASE_URL}/prescriptions/`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await r.json();

    const table = document.getElementById("prescriptionTable");

    data.forEach(p => {
        table.innerHTML += `
            <tr>
                <td>${p.title}</td>
                <td>${p.doctor_name}</td>
                <td>${p.date}</td>
                <td>${p.medicines.length}</td>
            </tr>
        `;
    });
}

/* ----------------- LOAD MEDICINES ----------------- */
async function loadMedicines() {
    const token = localStorage.getItem("token");

    const r = await fetch(`${BASE_URL}/medicine/all`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await r.json();

    const table = document.getElementById("medicineTable");

    data.forEach(m => {
        table.innerHTML += `
            <tr>
                <td>${m.name}</td>
                <td>${m.dosage}</td>
                <td>${m.frequency}</td>
                <td>${m.times.join(", ")}</td>
                <td>${m.start_date}</td>
                <td>${m.end_date}</td>
                <td>${m.prescription_id || "-"}</td>
            </tr>
        `;
    });
}
