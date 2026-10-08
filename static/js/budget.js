/* ==========================================
   BUDGET CALCULATOR
========================================== */

function calculateBudget() {

    // Get values from input fields
    let transport = parseFloat(document.getElementById("transport").value) || 0;
    let hotel = parseFloat(document.getElementById("hotel").value) || 0;
    let food = parseFloat(document.getElementById("food").value) || 0;
    let ticket = parseFloat(document.getElementById("ticket").value) || 0;

    // Calculate total
    let total = transport + hotel + food + ticket;

    // Display total
    document.getElementById("totalBudget").innerHTML =
        "₹ " + total.toLocaleString("en-IN");

}

/* ==========================================
   CLEAR FORM
========================================== */

function clearBudget() {

    document.getElementById("transport").value = "";
    document.getElementById("hotel").value = "";
    document.getElementById("food").value = "";
    document.getElementById("ticket").value = "";

    document.getElementById("totalBudget").innerHTML = "₹ 0";

}