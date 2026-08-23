/* =========================================================
   MEDRIPPLE
   Frontend Interaction Layer
   ========================================================= */

"use strict";


/* =========================================================
   API CONFIGURATION
   ========================================================= */

/*
 * Your FastAPI Swagger confirms:
 *
 * POST /api/v1/auth/register
 *
 * Therefore authentication endpoints use /api/v1/auth.
 *
 * Other API endpoints are kept separate because we have not
 * verified their exact prefixes from your Swagger yet.
 */

const AUTH_API = "/api/v1/auth";


/* =========================================================
   DOM HELPERS
   ========================================================= */

const $ = (selector, root = document) => {
  return root.querySelector(selector);
};


const $$ = (selector, root = document) => {
  return Array.from(root.querySelectorAll(selector));
};


/* =========================================================
   API HELPER
   ========================================================= */

async function apiFetch(url, options = {}) {

  const config = {
    credentials: "include",
    ...options
  };


  const token = localStorage.getItem("medripple_token");
  const reqHeaders = { ...(config.headers || {}) };
  if (token && !reqHeaders["Authorization"]) {
    reqHeaders["Authorization"] = `Bearer ${token}`;
  }

  /*
   * Only add JSON Content-Type when we are sending a body.
   * This prevents unnecessary headers on GET requests.
   */

  const isFormData =
    typeof FormData !== "undefined" &&
    config.body instanceof FormData;


  if (config.body && !isFormData && !reqHeaders["Content-Type"]) {
    reqHeaders["Content-Type"] = "application/json";
  }

  config.headers = reqHeaders;


  const response = await fetch(
    url,
    config
  );


  let data = {};


  try {

    data = await response.json();

  } catch {

    data = {};

  }


  if (response.status === 401) {

    localStorage.removeItem("medripple_token");

    if (
      !window.location.pathname.startsWith("/login") &&
      !window.location.pathname.startsWith("/register")
    ) {

      showToast(
        "Session expired or unauthenticated. Please log in.",
        "error"
      );

      setTimeout(() => {

        window.location.href = "/login";

      }, 600);

    }

    throw new Error("Authentication required. Please log in.");

  }


  if (!response.ok) {

    let message =
      data.detail ||
      data.message ||
      data.error?.message ||
      data.error ||
      "Something went wrong.";


    /*
     * FastAPI validation errors sometimes return:
     *
     * detail: [
     *   {
     *      loc: [...],
     *      msg: "...",
     *      type: "..."
     *   }
     * ]
     *
     * Convert that into something readable.
     */

    if (Array.isArray(message)) {

      message = message
        .map(error => {

          if (typeof error === "string") {
            return error;
          }

          return error.msg || "Invalid request.";

        })
        .join(", ");

    }

    if (message && typeof message === "object") {

      message =
        message.message ||
        message.detail ||
        "Something went wrong.";

    }


    throw new Error(message);

  }


  return data;

}


/* =========================================================
   PROFILE IMAGE UPLOAD
   ========================================================= */

const profileImageInput =
  $("#profile-image-input");


if (profileImageInput) {

  profileImageInput.addEventListener(
    "change",
    async () => {

      const [file] = profileImageInput.files || [];

      if (!file) {
        return;
      }

      const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
      ];


      if (!allowedTypes.includes(file.type)) {
        showToast(
          "Choose a JPEG, PNG, or WEBP image.",
          "error"
        );
        profileImageInput.value = "";
        return;
      }


      if (file.size > 5 * 1024 * 1024) {
        showToast(
          "Profile images must be 5 MB or smaller.",
          "error"
        );
        profileImageInput.value = "";
        return;
      }


      const formData = new FormData();
      formData.append("file", file);


      try {

        const data = await apiFetch(
          "/api/v1/profile/image",
          {
            method: "POST",
            body: formData
          }
        );


        const imageUrl =
          data.data?.presigned_url;


        const avatar = $("#profile-avatar");


        if (avatar && imageUrl) {
          avatar.src = imageUrl;
        }


        showToast(
          "Profile image saved.",
          "success"
        );


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


      } finally {

        profileImageInput.value = "";

      }

    }
  );

}


/* =========================================================
   TOAST SYSTEM
   ========================================================= */

function showToast(
  message,
  type = "info"
) {

  const container =
    $("#toast-container");


  if (!container) {
    return;
  }


  const toast =
    document.createElement("div");


  toast.className =
    `toast ${type}`;


  const icon =
    document.createElement("i");


  if (type === "success") {

    icon.className =
      "fa-solid fa-circle-check";

  } else if (type === "error") {

    icon.className =
      "fa-solid fa-circle-exclamation";

  } else {

    icon.className =
      "fa-solid fa-circle-info";

  }


  const text =
    document.createElement("span");


  text.textContent =
    message;


  toast.appendChild(icon);
  toast.appendChild(text);


  container.appendChild(toast);


  requestAnimationFrame(() => {

    toast.classList.add("show");

  });


  setTimeout(() => {

    toast.style.opacity =
      "0";

    toast.style.transform =
      "translateY(8px)";


    setTimeout(() => {

      toast.remove();

    }, 200);

  }, 3200);

}


/* =========================================================
   BUTTON LOADING STATE
   ========================================================= */

function setButtonLoading(
  button,
  loading,
  loadingText = "Working..."
) {

  if (!button) {
    return;
  }


  if (loading) {

    if (!button.dataset.originalHtml) {

      button.dataset.originalHtml =
        button.innerHTML;

    }


    button.disabled =
      true;


    button.innerHTML = `
      <i class="fa-solid fa-circle-notch fa-spin"></i>
      ${loadingText}
    `;

  } else {

    button.disabled =
      false;


    if (button.dataset.originalHtml) {

      button.innerHTML =
        button.dataset.originalHtml;

    }

  }

}


/* =========================================================
   MODALS
   ========================================================= */

function openModal(id) {

  const modal =
    document.getElementById(id);


  if (!modal) {
    return;
  }


  modal.classList.add("active");


  document.body.classList.add(
    "modal-open"
  );

}


function closeModal(id) {

  const modal =
    document.getElementById(id);


  if (!modal) {
    return;
  }


  modal.classList.remove(
    "active"
  );


  document.body.classList.remove(
    "modal-open"
  );

}


/* Close buttons */

$$("[data-modal-close]")
  .forEach(button => {

    button.addEventListener(
      "click",
      () => {

        closeModal(
          button.dataset.modalClose
        );

      }
    );

  });


/* Close when clicking backdrop */

$$(".modal-backdrop")
  .forEach(modal => {

    modal.addEventListener(
      "click",
      event => {

        if (
          event.target === modal
        ) {

          modal.classList.remove(
            "active"
          );


          document.body.classList.remove(
            "modal-open"
          );

        }

      }
    );

  });


/* Escape closes modal */

document.addEventListener(
  "keydown",
  event => {

    if (
      event.key !== "Escape"
    ) {
      return;
    }


    const activeModal =
      $(".modal-backdrop.active");


    if (activeModal) {

      activeModal.classList.remove(
        "active"
      );


      document.body.classList.remove(
        "modal-open"
      );

    }

  }
);


/* =========================================================
   LOGOUT
   ========================================================= */

const logoutButton =
  $("#logout-btn");


if (logoutButton) {

  logoutButton.addEventListener(
    "click",
    async () => {

      setButtonLoading(
        logoutButton,
        true,
        "Signing out..."
      );


      try {

        await apiFetch(
          `${AUTH_API}/logout`,
          {
            method: "POST"
          }
        );

        localStorage.removeItem("medripple_token");


        window.location.href =
          "/login";


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          logoutButton,
          false
        );

      }

    }
  );

}


/* =========================================================
   LOGIN
   ========================================================= */

const loginForm =
  $("#login-form");


if (loginForm) {

  loginForm.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const button =
        loginForm.querySelector(
          "button[type='submit']"
        );


      const email =
        $("#login-email")
          ?.value
          .trim();


      const password =
        $("#login-password")
          ?.value || "";


      if (!email) {

        showToast(
          "Please enter your email address.",
          "error"
        );

        return;

      }


      if (!password) {

        showToast(
          "Please enter your password.",
          "error"
        );

        return;

      }


      setButtonLoading(
        button,
        true,
        "Signing in..."
      );


      try {

        /*
         * Authentication API:
         *
         * POST /api/v1/auth/login
         */

        const data =
          await apiFetch(
            `${AUTH_API}/login`,
            {
              method: "POST",

              body:
                JSON.stringify({
                  email,
                  password
                })
            }
          );


        if (data.data && data.data.access_token) {
          localStorage.setItem("medripple_token", data.data.access_token);
        }

        showToast(
          data.message ||
          "Signed in successfully.",
          "success"
        );


        /*
         * If backend returns a redirect,
         * use it. Otherwise use role-based routing.
         */

        let redirect = data.redirect || data.redirect_url;
        
        if (!redirect && data.data && data.data.role) {
          if (data.data.role === "DOCTOR") {
            redirect = "/doctor/dashboard";
          } else if (data.data.role === "ADMIN") {
            redirect = "/admin/dashboard";
          } else {
            redirect = "/patient/dashboard";
          }
        } else if (!redirect) {
          redirect = "/patient/dashboard";
        }


        setTimeout(() => {

          window.location.href =
            redirect;

        }, 350);


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          button,
          false
        );

      }

    }
  );

}


/* =========================================================
   REGISTER
   ========================================================= */

const registerForm =
  $("#register-form");


const roleSelect =
  $("#reg-role");


const doctorFields =
  $("#doctor-extra-fields");


/* ---------------------------------------------------------
   Doctor field visibility
   --------------------------------------------------------- */

function updateDoctorFields() {

  if (
    !roleSelect ||
    !doctorFields
  ) {
    return;
  }


  const isDoctor =
    roleSelect.value === "DOCTOR";


  doctorFields.classList.toggle(
    "hidden",
    !isDoctor
  );


  const specialization =
    $("#reg-specialization");


  const license =
    $("#reg-license");


  if (specialization) {

    specialization.required =
      isDoctor;

  }


  if (license) {

    license.required =
      isDoctor;

  }

}


if (roleSelect) {

  roleSelect.addEventListener(
    "change",
    updateDoctorFields
  );


  updateDoctorFields();

}


/* ---------------------------------------------------------
   Registration
   --------------------------------------------------------- */

if (registerForm) {

  registerForm.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const button =
        registerForm.querySelector(
          "button[type='submit']"
        );


      /*
       * Read registration fields.
       */

      const name =
        $("#reg-name")
          ?.value
          .trim() || "";


      const email =
        $("#reg-email")
          ?.value
          .trim() || "";


      const phone =
        $("#reg-phone")
          ?.value
          .trim() || "";


      const password =
        $("#reg-password")
          ?.value || "";


      const role =
        $("#reg-role")
          ?.value || "PATIENT";


      const specialization =
        $("#reg-specialization")
          ?.value
          .trim() || "";


      const licenseNumber =
        $("#reg-license")
          ?.value
          .trim() || "";


      /* ---------------------------------------------------
         Client-side validation
         --------------------------------------------------- */

      if (!name) {

        showToast(
          "Please enter your full name.",
          "error"
        );

        return;

      }


      if (!email) {

        showToast(
          "Please enter your email address.",
          "error"
        );

        return;

      }


      if (!password) {

        showToast(
          "Please enter a password.",
          "error"
        );

        return;

      }


      if (role === "DOCTOR") {

        if (!specialization) {

          showToast(
            "Please enter your medical specialization.",
            "error"
          );

          return;

        }


        if (!licenseNumber) {

          showToast(
            "Please enter your medical license number.",
            "error"
          );

          return;

        }

      }


      /*
       * IMPORTANT
       *
       * Your Swagger screenshot confirms that
       * the backend expects:
       *
       * email
       * password
       * role
       * name
       * phone
       * specialization
       * license_number
       */

      const payload = {

        email:
          email,

        password:
          password,

        role:
          role,

        name:
          name,

        phone:
          phone,

        specialization:
          specialization,

        license_number:
          licenseNumber

      };


      setButtonLoading(
        button,
        true,
        "Creating account..."
      );


      try {

        /*
         * CONFIRMED FROM YOUR SWAGGER:
         *
         * POST /api/v1/auth/register
         */

        const data =
          await apiFetch(
            `${AUTH_API}/register`,
            {
              method: "POST",

              body:
                JSON.stringify(payload)
            }
          );


        showToast(
          data.message ||
          "Account created successfully.",
          "success"
        );


        /*
         * Backend may provide a redirect.
         */

        const redirect =
          data.redirect ||
          data.redirect_url ||
          "/login";


        setTimeout(() => {

          window.location.href =
            redirect;

        }, 500);


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          button,
          false
        );

      }

    }
  );

}


/* =========================================================
   DOCTOR SEARCH
   ========================================================= */

const doctorSearchForm =
  $("#search-doctors-form");


if (doctorSearchForm) {

  doctorSearchForm.addEventListener(
    "submit",
    event => {

      event.preventDefault();


      const query =
        $("#spec-input")
          ?.value
          .trim()
          .toLowerCase() || "";


      const cards =
        $$(".doctor-card");


      /*
       * If your doctor cards don't have
       * .doctor-card, fall back to cards
       * inside #doctors-grid.
       */

      const searchableCards =
        cards.length
          ? cards
          : $$("#doctors-grid .card");


      searchableCards.forEach(card => {

        const specialization =
          (
            card.dataset.specialization ||
            card.textContent ||
            ""
          ).toLowerCase();


        const name =
          (
            card.dataset.doctorName ||
            ""
          ).toLowerCase();


        const visible =
          !query ||
          specialization.includes(query) ||
          name.includes(query);


        card.style.display =
          visible
            ? ""
            : "none";

      });

    }
  );

}


/* =========================================================
   DOCTOR BOOKING
   ========================================================= */

let selectedDoctorId =
  null;


let selectedDoctorName =
  null;


let selectedSlot =
  null;


/* ---------------------------------------------------------
   Select doctor
   --------------------------------------------------------- */

$$(".select-doctor-btn")
  .forEach(button => {

    button.addEventListener(
      "click",
      () => {

        selectedDoctorId =
          button.dataset.doctorId;


        selectedDoctorName =
          button.dataset.doctorName;


        selectedSlot =
          null;


        const title =
          $("#modal-doc-title");


        if (title) {

          title.textContent =
            `Book with Dr. ${selectedDoctorName}`;

        }


        const dateInput =
          $("#booking-date");


        if (dateInput) {

          dateInput.value =
            "";

        }


        const slots =
          $("#slots-container");


        if (slots) {

          slots.innerHTML = `
            <span class="text-muted font-size-sm">
              Select a date to see available times.
            </span>
          `;

        }


        const symptoms =
          $("#symptoms-input");


        if (symptoms) {

          symptoms.value =
            "";

        }


        const confirm =
          $("#confirm-booking-btn");


        if (confirm) {

          confirm.disabled =
            true;

        }


        openModal(
          "booking-modal"
        );

      }
    );

  });


/* =========================================================
   LOAD AVAILABLE SLOTS
   ========================================================= */

const bookingDate =
  $("#booking-date");


if (bookingDate) {

  bookingDate.addEventListener(
    "change",
    async () => {

      if (!selectedDoctorId) {
        return;
      }


      const date =
        bookingDate.value;


      if (!date) {
        return;
      }


      const container =
        $("#slots-container");


      if (!container) {
        return;
      }


      container.innerHTML = `
        <span class="text-muted font-size-sm">
          Loading availability...
        </span>
      `;


      try {

        const data =
          await apiFetch(
            `/api/appointments/slots?doctor_id=${encodeURIComponent(selectedDoctorId)}&date=${encodeURIComponent(date)}`
          );


        const slots =
          data.slots || [];


        if (!slots.length) {

          container.innerHTML = `
            <span class="text-muted font-size-sm">
              No available times for this date.
            </span>
          `;

          return;

        }


        container.innerHTML =
          "";


        slots.forEach(slot => {

          const button =
            document.createElement(
              "button"
            );


          button.type =
            "button";


          button.className =
            "time-slot-btn";


          button.textContent =
            slot.display ||
            slot.start_time ||
            slot.time ||
            slot;


          button.dataset.slot =
            slot.id ||
            slot.start_time ||
            slot.time ||
            slot;


          button.addEventListener(
            "click",
            () => {

              $$(".time-slot-btn")
                .forEach(btn => {

                  btn.classList.remove(
                    "selected"
                  );

                });


              button.classList.add(
                "selected"
              );


              selectedSlot =
                button.dataset.slot;


              const confirm =
                $("#confirm-booking-btn");


              if (confirm) {

                confirm.disabled =
                  false;

              }

            }
          );


          container.appendChild(
            button
          );

        });


      } catch (error) {

        container.innerHTML = `
          <span class="text-rose font-size-sm">
            Unable to load availability.
          </span>
        `;


        showToast(
          error.message,
          "error"
        );

      }

    }
  );

}


/* =========================================================
   CONFIRM APPOINTMENT
   ========================================================= */

const confirmBooking =
  $("#confirm-booking-btn");


if (confirmBooking) {

  confirmBooking.addEventListener(
    "click",
    async () => {

      if (
        !selectedDoctorId ||
        !selectedSlot
      ) {

        showToast(
          "Please select a time slot.",
          "error"
        );

        return;

      }


      const symptoms =
        $("#symptoms-input")
          ?.value
          .trim() || "";


      setButtonLoading(
        confirmBooking,
        true,
        "Booking..."
      );


      try {

        await apiFetch(
          "/api/appointments/book",
          {
            method: "POST",

            body:
              JSON.stringify({

                doctor_id:
                  selectedDoctorId,

                slot_id:
                  selectedSlot,

                symptoms:
                  symptoms,

                reason:
                  symptoms

              })
          }
        );


        closeModal(
          "booking-modal"
        );


        showToast(
          "Appointment booked successfully.",
          "success"
        );


        setTimeout(() => {

          window.location.reload();

        }, 700);


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          confirmBooking,
          false
        );

      }

    }
  );

}


/* =========================================================
   AI SYMPTOM INTAKE
   ========================================================= */

const intakeForm =
  $("#ai-intake-form");


if (intakeForm) {

  intakeForm.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const button =
        intakeForm.querySelector(
          "button[type='submit']"
        );


      const symptoms =
        $("#raw-symptoms")
          ?.value
          .trim() || "";


      const appointmentId =
        intakeForm.dataset.appointmentId;


      if (!symptoms) {

        showToast(
          "Please describe your symptoms first.",
          "error"
        );

        return;

      }


      if (!appointmentId) {

        showToast(
          "Appointment information is missing.",
          "error"
        );

        return;

      }


      setButtonLoading(
        button,
        true,
        "Preparing..."
      );


      try {

        const data =
          await apiFetch(
            `/api/intake/${appointmentId}`,
            {
              method: "POST",

              body:
                JSON.stringify({
                  symptoms
                })
            }
          );


        const resultArea =
          $("#ai-result-area");


        if (resultArea) {

          resultArea.classList.remove(
            "hidden"
          );

        }


        const complaint =
          $("#chief-complaint-text");


        if (complaint) {

          complaint.textContent =
            data.chief_complaint ||
            data.summary ||
            "Your response has been organized for your clinician.";

        }


        const urgency =
          $("#urgency-badge");


        if (urgency) {

          const level =
            (
              data.urgency ||
              "REVIEW"
            ).toUpperCase();


          urgency.textContent =
            `URGENCY: ${level}`;


          urgency.className =
            `badge badge-${level.toLowerCase()}`;

        }


        renderList(
          $("#adaptive-questions-list"),
          data.adaptive_questions ||
          data.questions ||
          []
        );


        showToast(
          "Visit preparation complete.",
          "success"
        );


        if (resultArea) {

          resultArea.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });

        }


        setButtonLoading(
          button,
          false
        );


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          button,
          false
        );

      }

    }
  );

}


/* =========================================================
   RENDER LIST
   ========================================================= */

function renderList(
  element,
  items
) {

  if (!element) {
    return;
  }


  element.innerHTML =
    "";


  if (
    !items ||
    !items.length
  ) {

    const li =
      document.createElement(
        "li"
      );


    li.textContent =
      "No information available.";


    element.appendChild(
      li
    );


    return;

  }


  items.forEach(item => {

    const li =
      document.createElement(
        "li"
      );


    if (
      typeof item === "string"
    ) {

      li.textContent =
        item;

    } else {

      li.textContent =
        JSON.stringify(item);

    }


    li.className =
      "mb-1";


    element.appendChild(
      li
    );

  });

}


/* =========================================================
   DOCTOR AI COPILOT
   ========================================================= */

const regenBriefButton =
  $("#regen-brief-btn");


async function loadDoctorBrief() {

  if (!regenBriefButton) {
    return;
  }


  const appointmentId =
    regenBriefButton.dataset.apptId;


  if (!appointmentId) {

    showToast(
      "Appointment information is missing.",
      "error"
    );

    return;

  }


  const loading =
    $("#brief-loading");


  const content =
    $("#brief-content");


  if (loading) {

    loading.classList.remove(
      "hidden"
    );

  }


  if (content) {

    content.classList.add(
      "hidden"
    );

  }


  try {

    const data =
      await apiFetch(
        `/api/doctor/copilot/${appointmentId}`
      );


    const urgency =
      $("#brief-urgency");


    if (urgency) {

      const level =
        (
          data.urgency ||
          "REVIEW"
        ).toUpperCase();


      urgency.textContent =
        level;


      urgency.className =
        `badge badge-${level.toLowerCase()}`;

    }


    const complaint =
      $("#chief-complaint");


    if (complaint) {

      complaint.textContent =
        data.chief_complaint ||
        data.summary ||
        "No chief complaint available.";

    }


    renderList(
      $("#history-list"),
      data.history ||
      data.relevant_history ||
      []
    );


    renderList(
      $("#questions-list"),
      data.questions ||
      data.suggested_questions ||
      []
    );


    if (loading) {

      loading.classList.add(
        "hidden"
      );

    }


    if (content) {

      content.classList.remove(
        "hidden"
      );

    }


  } catch (error) {

    if (loading) {

      loading.textContent =
        "Unable to prepare the patient brief.";

    }


    showToast(
      error.message,
      "error"
    );

  }

}


if (regenBriefButton) {

  regenBriefButton.addEventListener(
    "click",
    async () => {

      setButtonLoading(
        regenBriefButton,
        true,
        "Refreshing..."
      );


      await loadDoctorBrief();


      setButtonLoading(
        regenBriefButton,
        false
      );

    }
  );


  loadDoctorBrief();

}


/* =========================================================
   FINALIZE CONSULTATION
   ========================================================= */

const finalizeButton =
  $("#finalize-consultation-btn");


if (finalizeButton) {

  finalizeButton.addEventListener(
    "click",
    async () => {

      const appointmentId =
        finalizeButton.dataset.apptId;


      const clinicalNotes =
        $("#clinical-notes")
          ?.value
          .trim() || "";


      const medication = {

        name:
          $("#med-name")
            ?.value
            .trim() || "",

        dosage:
          $("#med-dosage")
            ?.value
            .trim() || "",

        frequency:
          $("#med-freq")
            ?.value
            .trim() || "",

        duration:
          $("#med-duration")
            ?.value
            .trim() || "",

        instructions:
          $("#med-instructions")
            ?.value
            .trim() || ""

      };


      if (!appointmentId) {

        showToast(
          "Appointment information is missing.",
          "error"
        );

        return;

      }


      if (!clinicalNotes) {

        showToast(
          "Please enter the clinical notes.",
          "error"
        );

        return;

      }


      setButtonLoading(
        finalizeButton,
        true,
        "Finalizing..."
      );


      try {

        await apiFetch(
          `/api/doctor/consultation/${appointmentId}/finalize`,
          {
            method: "POST",

            body:
              JSON.stringify({

                clinical_notes:
                  clinicalNotes,

                medication:
                  medication

              })
          }
        );


        showToast(
          "Consultation completed successfully.",
          "success"
        );


        setTimeout(() => {

          window.location.href =
            "/doctor/dashboard";

        }, 700);


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


        setButtonLoading(
          finalizeButton,
          false
        );

      }

    }
  );

}


/* =========================================================
   MEDICATION ADHERENCE
   ========================================================= */

$$(".check-adherence-btn")
  .forEach(button => {

    button.addEventListener(
      "click",
      async () => {

        const prescriptionId =
          button.dataset.rxId;


        if (!prescriptionId) {

          showToast(
            "Prescription information is missing.",
            "error"
          );

          return;

        }


        const body =
          $("#adherence-body");


        if (body) {

          body.innerHTML = `
            <div class="text-muted">
              Loading adherence information...
            </div>
          `;

        }


        openModal(
          "adherence-modal"
        );


        try {

          const data =
            await apiFetch(
              `/api/medications/${prescriptionId}/adherence`
            );


          if (body) {

            const percentage =
              data.adherence_percentage ??
              data.percentage ??
              "—";


            const taken =
              data.taken ??
              "—";


            const missed =
              data.missed ??
              "—";


            body.innerHTML = `

              <div class="bento-grid">

                <div class="card col-span-4">

                  <div class="card-title">
                    Adherence
                  </div>

                  <div class="card-value text-primary mt-1">
                    ${percentage}%
                  </div>

                </div>


                <div class="card col-span-4">

                  <div class="card-title">
                    Taken
                  </div>

                  <div class="card-value text-emerald mt-1">
                    ${taken}
                  </div>

                </div>


                <div class="card col-span-4">

                  <div class="card-title">
                    Missed
                  </div>

                  <div class="card-value text-rose mt-1">
                    ${missed}
                  </div>

                </div>

              </div>

            `;

          }


        } catch (error) {

          if (body) {

            body.innerHTML = `
              <div class="text-rose">
                Unable to load adherence information.
              </div>
            `;

          }


          showToast(
            error.message,
            "error"
          );

        }

      }
    );

  });


/* =========================================================
   ACKNOWLEDGE MEDICATION DOSE
   ========================================================= */

$$(".ack-reminder-btn")
  .forEach(button => {

    button.addEventListener(
      "click",
      async () => {

        const scheduleId =
          button.dataset.schedId;


        if (!scheduleId) {

          showToast(
            "Medication schedule information is missing.",
            "error"
          );

          return;

        }


        setButtonLoading(
          button,
          true,
          "Saving..."
        );


        try {

          await apiFetch(
            `/api/medications/schedule/${scheduleId}/ack`,
            {
              method: "POST"
            }
          );


          const card =
            button.closest(
              ".care-plan-phase"
            );


          if (card) {

            card.style.opacity =
              "0.45";


            card.style.pointerEvents =
              "none";

          }


          showToast(
            "Dose recorded.",
            "success"
          );


        } catch (error) {

          showToast(
            error.message,
            "error"
          );


          setButtonLoading(
            button,
            false
          );

        }

      }
    );

  });


/* =========================================================
   DOCTOR LEAVE
   ========================================================= */

const leaveForm =
  $("#doctor-leave-form");


if (leaveForm) {

  leaveForm.addEventListener(
    "submit",
    async event => {

      event.preventDefault();


      const button =
        leaveForm.querySelector(
          "button[type='submit']"
        );


      const start =
        $("#leave-start")
          ?.value || "";


      const end =
        $("#leave-end")
          ?.value || "";


      const reason =
        $("#leave-reason")
          ?.value
          .trim() || "";


      if (!start || !end) {

        showToast(
          "Please select both dates.",
          "error"
        );

        return;

      }


      if (end < start) {

        showToast(
          "The end date cannot be before the start date.",
          "error"
        );

        return;

      }


      setButtonLoading(
        button,
        true,
        "Submitting..."
      );


      try {

        const data =
          await apiFetch(
            "/api/doctor/leave",
            {
              method: "POST",

              body:
                JSON.stringify({

                  start_date:
                    start,

                  end_date:
                    end,

                  reason:
                    reason

                })
            }
          );


        showToast(
          data.message ||
          "Leave submitted successfully.",
          "success"
        );


        leaveForm.reset();


      } catch (error) {

        showToast(
          error.message,
          "error"
        );


      } finally {

        setButtonLoading(
          button,
          false
        );

      }

    }
  );

}


/* =========================================================
   ADMIN DELETE DOCTOR
   ========================================================= */

$$(".delete-doctor-btn")
  .forEach(button => {

    button.addEventListener(
      "click",
      async () => {

        const doctorId =
          button.dataset.doctorId;


        if (!doctorId) {

          showToast(
            "Doctor information is missing.",
            "error"
          );

          return;

        }


        const confirmed =
          window.confirm(
            "Remove this doctor from MedRipple?"
          );


        if (!confirmed) {
          return;
        }


        setButtonLoading(
          button,
          true,
          "Removing..."
        );


        try {

          await apiFetch(
            `/api/admin/doctors/${doctorId}`,
            {
              method: "DELETE"
            }
          );


          const row =
            button.closest("tr");


          if (row) {

            row.style.opacity =
              "0";


            row.style.transform =
              "translateY(-4px)";


            setTimeout(() => {

              row.remove();

            }, 200);

          }


          showToast(
            "Doctor removed successfully.",
            "success"
          );


        } catch (error) {

          showToast(
            error.message,
            "error"
          );


          setButtonLoading(
            button,
            false
          );

        }

      }
    );

  });


/* =========================================================
   DATE HELPERS
   ========================================================= */

const today =
  new Date()
    .toISOString()
    .split("T")[0];


const bookingDateInput =
  $("#booking-date");


if (bookingDateInput) {

  bookingDateInput.min =
    today;

}


const leaveStart =
  $("#leave-start");


const leaveEnd =
  $("#leave-end");


if (leaveStart) {

  leaveStart.min =
    today;

}


if (leaveEnd) {

  leaveEnd.min =
    today;

}


/* =========================================================
   PASSWORD VISIBILITY
   ========================================================= */

$$("[data-password-toggle]")
  .forEach(button => {

    button.addEventListener(
      "click",
      () => {

        const targetId =
          button.dataset.passwordToggle;


        const input =
          document.getElementById(
            targetId
          );


        if (!input) {
          return;
        }


        const showing =
          input.type === "text";


        input.type =
          showing
            ? "password"
            : "text";


        const icon =
          button.querySelector("i");


        if (icon) {

          icon.className =
            showing
              ? "fa-regular fa-eye"
              : "fa-regular fa-eye-slash";

        }

      }
    );

  });


/* =========================================================
   FORM INPUT FEEDBACK
   ========================================================= */

$$(".form-control")
  .forEach(input => {

    input.addEventListener(
      "input",
      () => {

        input.classList.remove(
          "input-error"
        );

      }
    );

  });


/* =========================================================
   INITIALIZATION
   ========================================================= */

console.log(
  "%cMedRipple",
  "font-weight:800;font-size:18px;color:#147d70"
);

console.log(
  "%cClinical care, connected.",
  "font-size:12px;color:#64748b"
);

/* =========================================================
   AI CHAT WIDGET
   ========================================================= */

let chatHistory = [];
const aiEndpoint = window.location.pathname.startsWith("/doctor") ? "/api/v1/ai/chat/doctor" : "/api/v1/ai/chat/patient";
const patientIdMatch = window.location.pathname.match(/\/doctor\/copilot\/(\d+)/);
const targetPatientId = patientIdMatch ? parseInt(patientIdMatch[1]) : null;

function toggleChat() {
  const body = document.getElementById("chat-body");
  const icon = document.getElementById("chat-toggle-icon");
  if (body.style.display === "none") {
    body.style.display = "flex";
    icon.classList.replace("fa-chevron-up", "fa-chevron-down");
  } else {
    body.style.display = "none";
    icon.classList.replace("fa-chevron-down", "fa-chevron-up");
  }
}

function handleChatEnter(e) {
  if (e.key === "Enter") sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  
  const msgContainer = document.getElementById("chat-messages");
  
  // Add user message to UI
  msgContainer.innerHTML += `<div class="message user-message">${text}</div>`;
  input.value = "";
  msgContainer.scrollTop = msgContainer.scrollHeight;
  
  const payload = {
    message: text,
    history: chatHistory,
    patient_id: targetPatientId || 1 // Fallback for testing on doctor dashboard without specific patient
  };

  try {
    const data = await apiFetch(aiEndpoint, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    
    // Add AI message to UI
    msgContainer.innerHTML += `<div class="message ai-message">${data.data.reply}</div>`;
    msgContainer.scrollTop = msgContainer.scrollHeight;
    
    // Update history
    chatHistory.push({role: "user", content: text});
    chatHistory.push({role: "assistant", content: data.data.reply});
  } catch (error) {
    msgContainer.innerHTML += `<div class="message ai-message text-danger">Error: ${error.message}</div>`;
  }
}

async function deleteAppointment(appointmentId) {
  if (!confirm("Are you sure you want to permanently delete this completed appointment from your history?")) {
    return;
  }
  
  try {
    const data = await apiFetch(`/api/v1/appointments/${appointmentId}`, {
      method: "DELETE"
    });
    
    if (data.success) {
      window.location.reload();
    }
  } catch (error) {
    alert("Error deleting appointment: " + error.message);
  }
}
