document.addEventListener("DOMContentLoaded", () => {
  const faqHeaders = document.querySelectorAll(".faq-header");

  faqHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const faqBlock = this.parentNode;
      const faqBody = this.nextElementSibling;

      if (faqBlock.classList.contains("active")) {
        faqBody.style.height = "0px"; // Cierra el acordeón
        faqBlock.classList.remove("active");
      } else {
        // Cierra todos los otros acordeones
        document.querySelectorAll(".faq-block").forEach((block) => {
          block.classList.remove("active");
          block.querySelector(".faq-body").style.height = "0px";
        });

        // Abre este acordeón
        faqBody.style.height = faqBody.scrollHeight + "px";
        faqBlock.classList.add("active");
      }
    });
  });

  // Código para abrir automáticamente el primer acordeón si no se abre
  const firstFaqBody = document.querySelector(
    ".faq-wrapper .faq-block.active .faq-body"
  );
  if (firstFaqBody) {
    firstFaqBody.style.height = firstFaqBody.scrollHeight + "px"; // Asegúrate de que esta línea está aquí
  }
});
