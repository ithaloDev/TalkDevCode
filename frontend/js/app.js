import { api } from "./core/api.js";
import { Session } from "./core/session.js";
import { ThemeController } from "./ui/theme.js";
import { toast, refreshRelativeTimes } from "./ui/feedback.js";
import { PostsController } from "./features/posts.js";
import { CommentsController } from "./features/comments.js";

class TalkDevApp {
  constructor() {
    this.theme = new ThemeController(document.getElementById("theme-toggle"));
    this.posts = new PostsController();
    this.comments = new CommentsController();
    this.syncSession();
    this.bindGlobalEvents();
    document.getElementById("current-year").textContent = String(new Date().getFullYear());
    this.relativeTimeTimer = window.setInterval(() => refreshRelativeTimes(), 15_000);
    window.addEventListener("pagehide", () => window.clearInterval(this.relativeTimeTimer), { once: true });
    this.posts.loadPosts().then(() => {
      const params = new URLSearchParams(window.location.search);
      const postId = params.get("post");
      if (postId) {
        const existing = this.posts.posts.find(post => post.id === postId);
        if (existing) this.posts.selectPost(postId);
        else api.get(`/posts/${postId}`).then(post => { this.posts.posts.unshift(post); this.posts.renderFeed(); this.posts.selectPost(postId); }).catch(error => toast(error.message, "error"));
      }
      if (params.get("published") === "1") toast("Artigo publicado com sucesso.");
      if (params.has("post") || params.has("published")) history.replaceState({}, "", window.location.pathname);
    });
  }

  syncSession() {
    const authenticated = Session.isAuthenticated;
    document.getElementById("login-link")?.classList.toggle("hidden", authenticated);
    document.getElementById("register-link")?.classList.toggle("hidden", authenticated);
    document.getElementById("user-menu")?.classList.toggle("hidden", !authenticated);
    document.getElementById("new-post-button")?.classList.toggle("hidden", !authenticated);
    document.getElementById("profile-link")?.classList.toggle("hidden", !authenticated);
    if (authenticated) {
      document.getElementById("user-name").textContent = `@${Session.user.username}`;
      document.getElementById("user-avatar").textContent = "";
      document.getElementById("user-avatar").style.backgroundImage = `url("https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(Session.user.username + "_" + Session.user?.id).slice(0,8)}")`;
    }
    this.comments.updateSessionState();
  }

  bindGlobalEvents() {
    document.getElementById("logout-button")?.addEventListener("click", () => {
      Session.end();
      this.syncSession();
      this.comments.updateSessionState();
      toast("Você saiu da sua conta.");
      if (this.posts.selectedPostId) this.posts.selectPost(this.posts.selectedPostId);
    });
    const searchToggle = document.getElementById("search-toggle");
    searchToggle?.addEventListener("click", () => {
      const header = document.querySelector(".site-header");
      const open = header.classList.toggle("search-open");
      searchToggle.setAttribute("aria-expanded", String(open));
      searchToggle.setAttribute("aria-label", open ? "Fechar pesquisa" : "Abrir pesquisa");
      if (open) document.getElementById("search-input").focus();
    });
    const menu = document.getElementById("mobile-menu-toggle");
    menu?.addEventListener("click", () => {
      const sidebar = document.getElementById("feed-sidebar");
      const open = sidebar.classList.toggle("open");
      menu.setAttribute("aria-expanded", String(open));
      menu.setAttribute("aria-label", open ? "Fechar lista de artigos" : "Abrir lista de artigos");
    });
    // Atalho "/" leva o foco para a pesquisa.
    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
        event.preventDefault();
        document.getElementById("search-input").focus();
      }
      if (event.key === "Escape") document.getElementById("feed-sidebar")?.classList.remove("open");
    });
    // Token expirado ou revogado encerra a sessão local.
    document.addEventListener("talkdev:unauthorized", () => {
      Session.end();
      this.syncSession();
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  try { new TalkDevApp(); }
  catch (error) {
    console.error("Falha ao inicializar TalkDevCode:", error);
    toast("Não foi possível iniciar a aplicação.", "error");
  }
});
