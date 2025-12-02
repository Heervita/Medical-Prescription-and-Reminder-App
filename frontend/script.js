const BASE_URL = "http://127.0.0.1:8000";

// navigation & auth helpers (global)
function goTo(page){ window.location.href = page; }
function logout(){ localStorage.removeItem("token"); localStorage.removeItem("name"); window.location.href = "index.html"; }

// AUTH
async function signup(){
  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  try{
    const r = await fetch(`${BASE_URL}/auth/signup`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({name,email,password})
    });
    const data = await r.json();
    document.getElementById("message").innerText = data.message || "Account created";
    localStorage.setItem("name", name);
    setTimeout(()=> window.location.href="index.html",700);
  }catch(e){ document.getElementById("message").innerText = "Network error"; }
}

async function login(){
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  try{
    const r = await fetch(`${BASE_URL}/auth/login`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({email,password})
    });
    const data = await r.json();
    if(data.token){
      localStorage.setItem("token", data.token);
      localStorage.setItem("name", email.split("@")[0]);
      window.location.href = "dashboard.html";
    } else {
      document.getElementById("message").innerText = data.detail || "Invalid credentials";
    }
  }catch(e){ document.getElementById("message").innerText = "Network error"; }
}

// PRESCRIPTIONS
async function addPrescription(){
  const token = localStorage.getItem("token");
  if(!token) return alert("Please login again.");
  const title = document.getElementById("title").value;
  const doctor_name = document.getElementById("doctor_name").value;
  const date = document.getElementById("date").value;
  const r = await fetch(`${BASE_URL}/prescriptions/`, {
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`},
    body: JSON.stringify({title,doctor_name,date})
  });
  const data = await r.json();
  document.getElementById("message").innerText = data.id ? "Prescription added!" : (data.detail || "Error");
  if(data.id) localStorage.setItem("last_prescription_id", data.id);
}

// MEDICINES
async function addMedicine(){
  const token = localStorage.getItem("token");
  if(!token) return alert("Please login again.");
  const prescription_id = document.getElementById("prescription_id").value;
  const name = document.getElementById("name").value;
  const dosage = document.getElementById("dosage").value;
  const frequency = parseInt(document.getElementById("frequency").value) || 1;
  const times = document.getElementById("times").value.split(",").map(t=>t.trim()).filter(Boolean);
  const start_date = document.getElementById("start_date").value;
  const end_date = document.getElementById("end_date").value;
  const r = await fetch(`${BASE_URL}/medicine/`, {
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`},
    body: JSON.stringify({prescription_id,name,dosage,frequency,times,start_date,end_date})
  });
  const data = await r.json();
  document.getElementById("message").innerText = data.id ? "Medicine added!" : (data.detail || "Error");
}

// Quick previews (used on dashboard)
async function loadPrescriptionsPreview(){
  const token = localStorage.getItem("token");
  if(!token) return;
  const r = await fetch(`${BASE_URL}/prescriptions/`, {headers:{"Authorization":`Bearer ${token}`}});
  const data = await r.json();
  const node = document.getElementById("recentList");
  if(!node) return;
  node.innerHTML = "";
  data.slice(0,4).forEach(p=>{
    const el = document.createElement("div");
    el.className = "tiny-card";
    el.style.marginBottom="8px";
    el.innerHTML = `<strong>${p.title}</strong><div style="color:rgba(255,255,255,0.6)">${p.doctor_name} • ${p.date}</div>`;
    node.appendChild(el);
  });
}

async function loadMedicinesPreview(){
  const token = localStorage.getItem("token");
  if(!token) return;
  const r = await fetch(`${BASE_URL}/medicine/all`, {headers:{"Authorization":`Bearer ${token}`}});
  const data = await r.json();
  const node = document.getElementById("medPreview");
  if(!node) return;
  if(!data || data.length===0){ node.innerText = "No medicines yet"; return; }
  node.innerHTML = data.slice(0,6).map(m=>`<div style="padding:8px 0;border-bottom:1px dashed rgba(255,255,255,0.03)"><strong>${m.name}</strong> — ${m.dosage} <div style="color:rgba(255,255,255,0.6);font-size:12px">${m.times.join(", ")}</div></div>`).join("");
}
