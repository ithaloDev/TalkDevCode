import { api } from "./core/api.js";
import { Session } from "./core/session.js";
import { ThemeController } from "./ui/theme.js";

class NewPostPage {
  constructor() {
    // Tema dark & light
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
      new ThemeController(themeToggle)
    }

    this.form = document.getElementById("editor-form");
    this.btnSubmit = document.getElementById("btnSubmit");

    if (!Session.isAuthenticated) {
      window.location.href = "auth.html?next=new-post";
      return;
    }

    this.form?.addEventListener("submit", (event) => {
      event.preventDefault();
      event.stopPropagation();
    });

    this.btnSubmit?.addEventListener("click", async () => await this.submit())
  }

  async submit() {
    const error = document.getElementById("editor-error");
    const data = new FormData(this.form);

    const payload = { 
      title: String(data.get("title")).trim(), 
      content: String(data.get("content")).trim() 
    };

    if (!this.btnSubmit) return;

    if (!payload.title || !payload.content) return;

    this.btnSubmit.disabled = true; 
    this.btnSubmit.textContent = "Publicando..."; 
    error.textContent = "";

    try {
      await api.post("/posts/", payload, { token: Session.token });
      window.location.replace(new URL("../", window.location.href).href);
      
    } catch (exception) {
      error.textContent = exception.message;
    } finally {
      this.btnSubmit.disabled = false; 
      this.btnSubmit.textContent = "Publicar artigo";
    }
  }
}

new NewPostPage();
