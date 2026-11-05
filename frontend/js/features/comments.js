import { api } from "../core/api.js";
import { APP_STATE } from "../core/global.js";
import { Session } from "../core/session.js";
import { toast, formatDate } from "../ui/feedback.js";

export class CommentsController {
  constructor() {
    this.postId = null;
    this.comments = [];
    this.loadVersion = 0;
    this.submitting = false;
    this.form = document.getElementById("comment-form");
    this.list = document.getElementById("comments-list");
    this.bindEvents();
    document.addEventListener("talkdev:post-selected", (event) => this.load(event.detail.post.id));
    document.addEventListener("talkdev:post-closed", () => { this.postId = null; this.comments = []; this.loadVersion++; });
  }

  bindEvents() {
    this.form?.addEventListener("submit", (event) => {
      // Captura o submit antes dos listeners de bubbling e cancela a navegação nativa.
      event.preventDefault();
      event.stopImmediatePropagation();
      void this.create(event);
    }, { capture: true });
    this.list?.addEventListener("click", (event) => {
      const remove = event.target.closest("[data-comment-delete]");
      const reply = event.target.closest("[data-comment-reply]");
      if (remove) this.remove(remove.dataset.commentDelete);
      if (reply) this.startReply(reply.dataset.commentReply, reply.dataset.username);
    });
  }

  updateSessionState() {
    const authenticated = Session.isAuthenticated;
    const textarea = this.form?.querySelector("textarea");
    const submit = this.form?.querySelector('[type="submit"]');
    if (textarea) textarea.disabled = !authenticated;
    if (submit) submit.disabled = !authenticated;
    const hint = document.getElementById("comment-hint");
    if (hint) hint.textContent = authenticated ? "Mantenha a conversa respeitosa e construtiva." : "Entre na sua conta para comentar.";
  }

  async load(postId) {
    this.postId = postId;
    const version = ++this.loadVersion;
    this.updateSessionState();
    this.list.replaceChildren();
    const loading = document.createElement("p"); 
    loading.className = "sidebar-note"; 
    loading.textContent = "Carregando comentários..."; 
    this.list.append(loading);
    try {
      const data = await api.get(`/comments/post/${postId}?limit=${APP_STATE.Comments.limit}&offset=${APP_STATE.Comments.offset}`);
      if (version !== this.loadVersion || this.postId !== postId) return;
      this.comments = data;
      this.render();
    } catch (error) {
      if (version !== this.loadVersion) return;
      this.list.replaceChildren(); 
      toast(error.message, "error");
    }
  }

  avatar(username, className = "comment-avatar") {
    const img = document.createElement("img");
    username = `${username}_${Session.user?.id}`.slice(0,8);
    img.className = className; 
    img.alt = ""; 
    img.loading = "lazy";
    img.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(username)}`;
    return img;
  }

  render() {
    this.list.replaceChildren();
    document.getElementById("comments-count").textContent = String(this.comments.length);
    if (!this.comments.length) { 
      const empty = document.createElement("p"); 
      empty.className = "sidebar-note"; 
      empty.textContent = "Seja a primeira pessoa a comentar."; 
      this.list.append(empty); 
      return; 
    }

    const children = new Map();
    this.comments.forEach(comment => { 
      const key = comment.parent_id || "root"; 
      if (!children.has(key)) 
        children.set(key, []); 
      
      children.get(key).push(comment); });

    const fragment = document.createDocumentFragment();
    const appendTree = (comment, target, depth = 0) => {
      const item = document.createElement("article");
      item.className = `comment-item${depth ? " comment-reply" : ""}`;
      item.style.setProperty("--comment-depth", String(Math.min(depth, 4)));
      const username = comment.author?.username;
      const main = document.createElement("div"); main.className = "comment-main";
      const meta = document.createElement("div"); meta.className = "comment-meta";
      const name = document.createElement("strong"); name.textContent = `@${username}`;
      const time = document.createElement("time"); time.dateTime = comment.created_at; time.dataset.relativeTime = "true"; 
      time.textContent = formatDate(comment.created_at);

      meta.append(name, time);

      if (comment.parent_author?.username) { 
        const replied = document.createElement("span"); 
        replied.className = "reply-context"; 
        replied.textContent = `@respondeu @${comment.parent_author.username}`; 
        main.append(replied); }

      const text = document.createElement("p"); text.className = "comment-text"; text.textContent = comment.content;

      main.append(meta, text);

      const actions = document.createElement("div"); actions.className = "comment-actions";

      if (Session.isAuthenticated) { 
        const reply = document.createElement("button"); 
        reply.type = "button"; 
        reply.className = "comment-action"; 
        reply.dataset.commentReply = comment.id; 
        reply.dataset.username = username; 
        reply.textContent = "Responder"; 
        actions.append(reply); 
      }

      if (Session.user?.id === comment.user_id) { 
        const del = document.createElement("button"); 

        del.type = "button"; 
        del.className = "comment-action comment-delete"; 
        del.dataset.commentDelete = comment.id; 
        del.textContent = "Excluir"; 
        actions.append(del); 
      }

      main.append(actions);

      item.append(this.avatar(username), main); 
      target.append(item);
      (children.get(comment.id) || []).forEach(child => appendTree(child, target, depth + 1));
    };

    (children.get("root") || []).forEach(comment => appendTree(comment, fragment));

    // Orphaned replies are still visible if their parent was removed from a partial result.
    const rendered = new Set(this.comments.filter(c => !c.parent_id).map(c => c.id));
    if (!rendered.size) this.comments.forEach(c => appendTree(c, fragment));

    this.list.append(fragment);
  }

  startReply(commentId, username) {
    const textarea = this.form.querySelector("textarea");
    this.form.dataset.parentId = commentId;
    document.getElementById("comment-hint").textContent = `Respondendo a @${username}. Clique em cancelar para comentar no nível principal.`;
    let cancel = document.getElementById("cancel-reply");
    if (!cancel) { cancel = document.createElement("button"); cancel.id = "cancel-reply"; cancel.type = "button"; cancel.className = "comment-action"; cancel.textContent = "Cancelar resposta"; this.form.querySelector(".form-footer").prepend(cancel); cancel.addEventListener("click", () => this.clearReply()); }
    textarea.focus();
  }

  clearReply() { delete this.form.dataset.parentId; document.getElementById("cancel-reply")?.remove(); this.updateSessionState(); }

  async create(event) {
    // Impede o submit nativo mesmo se o handler for chamado por outro controle.
    event.preventDefault();
    event.stopPropagation();
    if (this.submitting) return;
    if (!Session.token) {
      toast("Entre na sua conta para comentar.", "error");
      return;
    }
    const textarea = this.form.querySelector("textarea");
    const content = textarea.value.trim();
    const postId = this.postId;
    if (!content || !postId) return;

    const submit = this.form.querySelector('[type="submit"]');
    const parentId = this.form.dataset.parentId || null;
    this.submitting = true;
    if (submit) { submit.disabled = true; submit.textContent = "Enviando..."; }
    try {
      const payload = { post_id: postId, content, ...(parentId ? { parent_id: parentId } : {}) };
      const comment = await api.post("/comments/", payload, { token: Session.token });
      // Não injeta a resposta em outro artigo caso o usuário tenha navegado durante o POST.
      if (this.postId === postId) {
        if (!this.comments.some((item) => item.id === comment.id)) this.comments.push(comment);
        textarea.value = "";
        this.clearReply();
        this.render();
      }
      toast("Comentário enviado.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      this.submitting = false;
      if (submit) { submit.disabled = !Session.isAuthenticated; submit.textContent = "Enviar comentário"; }
    }
  }

  async remove(commentId) {
    if (!Session.token || !window.confirm("Excluir este comentário e suas respostas?")) return;
    try {
      await api.delete(`/comments/${commentId}`, { token: Session.token }); const removed = new Set([commentId]);
      let changed = true;
      while (changed) { changed = false; this.comments.forEach(item => { if (item.parent_id && removed.has(item.parent_id) && !removed.has(item.id)) { removed.add(item.id); changed = true; } }); }
      this.comments = this.comments.filter(item => !removed.has(item.id)); this.render(); toast("Comentário excluído.");
    }
    catch (error) { toast(error.message, "error"); }
  }
}
