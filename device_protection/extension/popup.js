document.addEventListener("DOMContentLoaded", () => {
  const parentGateBtn = document.getElementById("parentGateBtn");
  const pinBox = document.getElementById("pinBox");
  const pinInput = document.getElementById("pinInput");
  const verifyPinBtn = document.getElementById("verifyPinBtn");
  const pinFeedback = document.getElementById("pinFeedback");

  parentGateBtn.addEventListener("click", () => {
    pinBox.style.display = pinBox.style.display === "block" ? "none" : "block";
  });

  verifyPinBtn.addEventListener("click", async () => {
    const pin = pinInput.value.trim();
    if (!pin) {
      pinFeedback.innerText = "Please enter 4-digit PIN.";
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/parents/verify-pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin })
      });
      const data = await res.json();
      if (data.verified || pin === "1234") {
        pinFeedback.style.color = "#34BFA3";
        pinFeedback.innerText = "Parent unlocked! Opening EduFeedia Parent Hub...";
        setTimeout(() => {
          chrome.tabs.create({ url: "http://127.0.0.1:5173/?mode=parent" });
        }, 800);
      } else {
        pinFeedback.style.color = "#FF7A59";
        pinFeedback.innerText = "Incorrect PIN. Default demo PIN is 1234.";
      }
    } catch (e) {
      if (pin === "1234") {
        pinFeedback.style.color = "#34BFA3";
        pinFeedback.innerText = "Verified! Opening Parent Hub...";
        chrome.tabs.create({ url: "http://127.0.0.1:5173/?mode=parent" });
      } else {
        pinFeedback.innerText = "Verification failed. Check local server.";
      }
    }
  });
});
