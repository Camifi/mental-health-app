let currentStep = 0;
const steps = document.querySelectorAll(".step");

function showStep(step) {
  steps.forEach((el, i) => {
    if (i === step) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

function nextStep() {
  if (currentStep < steps.length - 1) {
    currentStep++;
    showStep(currentStep);
  }
}

// Iniciar mostrando el primer paso
showStep(currentStep);
