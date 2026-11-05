import { api } from "./core/api.js";
import { Session } from "./core/session.js";
import { ThemeController } from "./ui/theme.js";
import { toast } from "./ui/feedback.js";

class AuthPage {
  constructor() {
    this.mode = new URLSearchParams(window.location.search).get("mode") === "register" ? "register" : "login";
    this.form = document.getElementById("auth-form");
    this.theme = new ThemeController(document.getElementById("theme-toggle"));
    this.bindEvents();
    this.setMode(this.mode);
  }

  bindEvents() {
    document.querySelectorAll("[data-mode], [data-switch]").forEach((button) => {
      button.addEventListener("click", () => this.setMode(button.dataset.mode || button.dataset.switch));
    });
    this.form.addEventListener("submit", (event) => this.submit(event));
  }

  setMode(mode) {
    this.mode = mode === "register" ? "register" : "login";
    const registering = this.mode === "register";
    document.getElementById("email-group").classList.toggle("hidden", !registering);
    document.getElementById("email").required = registering;
    document.getElementById("password").autocomplete = registering ? "new-password" : "current-password";
    document.getElementById("login-tab").classList.toggle("active", !registering);
    document.getElementById("register-tab").classList.toggle("active", registering);
    document.getElementById("login-tab").setAttribute("aria-selected", String(!registering));
    document.getElementById("register-tab").setAttribute("aria-selected", String(registering));
    document.getElementById("auth-title").textContent = registering ? "Faça parte da comunidade." : "Bom ter você por aqui.";
    document.getElementById("auth-description").textContent = registering
      ? "Crie sua conta e compartilhe conhecimento."
      : "Entre para acompanhar ideias e conversas.";
    document.getElementById("auth-submit").textContent = registering ? "Criar conta" : "Entrar";
    document.getElementById("auth-switch").innerHTML = registering
      ? 'Já tem uma conta? <button type="button" data-switch="login">Entrar</button>'
      : 'Ainda não tem conta? <button type="button" data-switch="register">Criar conta</button>';
    document.getElementById("auth-switch").querySelector("button").addEventListener("click", () => this.setMode(registering ? "login" : "register"));
    document.getElementById("auth-error").textContent = "";
  }

  async submit(event) {
    event.preventDefault();
    const formData = new FormData(this.form);
    const username = String(formData.get("username")).trim();
    const password = String(formData.get("password"));
    const submit = document.getElementById("auth-submit");
    const errorBox = document.getElementById("auth-error");
    errorBox.textContent = "";

    if (username.length < 3 || !/^[A-Za-z0-9_.-]+$/.test(username)) {
      errorBox.textContent = "Informe um nome de usuário válido (3 a 50 caracteres).";
      return;
    }
    if (password.length < 8 || new TextEncoder().encode(password).length > 72) {
      errorBox.textContent = "A senha deve possuir entre 8 e 72 bytes.";
      return;
    }

    submit.disabled = true;
    submit.textContent = "Aguarde...";
    try {
      if (this.mode === "register") {
        const email = String(formData.get("email")).trim();
        await api.post("/users/register", { username, email, password });
      }
      const tokenResponse = await api.post("/users/login", { username, password });
      const user = await api.get("/users/me", { token: tokenResponse.access_token });
      Session.start(tokenResponse.access_token, user);
      toast(this.mode === "register" ? "Conta criada. Bem-vindo!" : "Login realizado.");
      const next = new URLSearchParams(window.location.search).get("next");
      window.location.href = next === "new-post" ? "new-post.html" : "../";
    } catch (error) {
      errorBox.textContent = error.message;
    } finally {
      submit.disabled = false;
      submit.textContent = this.mode === "register" ? "Criar conta" : "Entrar";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new AuthPage());
