import { api } from "./core/api.js";
import { Session } from "./core/session.js";
import { ThemeController } from "./ui/theme.js";
import { toast, formatDate, refreshRelativeTimes } from "./ui/feedback.js";

class ProfilePage {
  constructor() {
    new ThemeController(document.getElementById("theme-toggle"));
    this.relativeTimeTimer = window.setInterval(() => refreshRelativeTimes(), 15_000);
    window.addEventListener("pagehide", () => window.clearInterval(this.relativeTimeTimer), { once: true });
    if (!Session.isAuthenticated) { window.location.href = "auth.html"; return; }
    this.load();
  }

  async load() {
    try {
      const activity = await api.get("/users/me/activity", { token: Session.token });
      const username = activity.user.username;
      document.getElementById("profile-name").textContent = `@${username}`;
      document.getElementById("profile-avatar").src = `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(username)}`;
      document.getElementById("profile-summary").textContent = `${activity.posts.length} artigos publicados · ${activity.comments.length} comentários`;
      this.renderPosts(activity.posts);
      this.renderComments(activity.comments);
    } catch (error) { toast(error.message, "error"); document.getElementById("profile-summary").textContent = "Não foi possível carregar o perfil."; }
  }

  renderPosts(posts) {
    const target = document.getElementById("profile-posts"); target.replaceChildren();
    if (!posts.length) { target.textContent = "Você ainda não publicou artigos."; return; }
    posts.forEach(post => {
      const item = document.createElement("article"); item.className = "activity-item";
      const link = document.createElement("a"); link.href = `../?post=${encodeURIComponent(post.id)}`; link.textContent = post.title;
      const date = document.createElement("time"); date.className = "form-hint"; date.dateTime = post.created_at; date.dataset.relativeTime = "true"; date.textContent = formatDate(post.created_at);
      item.append(link, date); target.append(item);
    });
  }

  renderComments(comments) {
    const target = document.getElementById("profile-comments"); target.replaceChildren();
    if (!comments.length) { target.textContent = "Você ainda não participou de uma conversa."; return; }
    comments.forEach(comment => {
      const item = document.createElement("article"); item.className = "activity-item";
      const title = document.createElement("a"); title.href = `../?post=${encodeURIComponent(comment.post_id)}`; title.textContent = comment.post_title;
      const content = document.createElement("p"); content.textContent = comment.content;
      const meta = document.createElement("p"); meta.className = "form-hint";
      const date = document.createElement("time"); date.dateTime = comment.created_at; date.dataset.relativeTime = "true"; date.textContent = formatDate(comment.created_at);
      meta.append(date, document.createTextNode(comment.parent_username ? ` · em resposta a @${comment.parent_username}` : ""));
      item.append(title, content, meta); target.append(item);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => new ProfilePage());
