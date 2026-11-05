import { api } from "../core/api.js";
import { APP_STATE } from "../core/global.js";
import { Session } from "../core/session.js";
import { toast, formatDate } from "../ui/feedback.js";

export class PostsController {
  constructor() {
    this.posts = [];
    this.selectedPostId = null;
    this.loading = false;
    this.hasMore = true;
    this.searchTerm = "";
    this.searchTimer = null;
    this.searchVersion = 0;
    this.editingPostId = null;
    this.listController = null;
    this.feed = document.getElementById("feed-list");
    this.article = document.getElementById("article-view");
    this.loadMoreButton = document.getElementById("load-more");
    this.modal = document.getElementById("post-modal");
    this.form = document.getElementById("post-form");
    this.bindEvents();
  }

  bindEvents() {
    this.feed?.addEventListener("click", (event) => {
      const card = event.target.closest("[data-post-id]");
      if (card) this.selectPost(card.dataset.postId);
    });
    this.loadMoreButton?.addEventListener("click", () => this.loadPosts());
    document.getElementById("refresh-posts")?.addEventListener("click", () => this.refresh());
    this.modal?.addEventListener("close", () => {
      this.editingPostId = null;
      this.form.reset();
      document.getElementById("post-modal-title").textContent = "Novo artigo";
    });
    this.modal?.querySelectorAll("[data-close-modal]").forEach((button) => {
      button.addEventListener("click", () => {
        this.modal.close();
        this.editingPostId = null;
        this.form.reset();
        document.getElementById("post-modal-title").textContent = "Novo artigo";
      });
    });
    this.form?.addEventListener("submit", (event) => this.createPost(event));
    document.getElementById("search-form")?.addEventListener("submit", (event) => event.preventDefault());
    document.getElementById("search-input")?.addEventListener("input", (event) => {
      this.searchTerm = event.target.value.trim();
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.searchPosts(), 250);
    });
    document.getElementById("close-article")?.addEventListener("click", () => this.closeArticle());
    this.article?.addEventListener("click", (event) => {
      const action = event.target.closest("[data-post-action]");
      if (action) this.handlePostAction(action.dataset.postAction);
    });
  }

  async refresh() {
    clearTimeout(this.searchTimer);
    this.searchVersion++;
    this.listController?.abort();
    this.listController = null;
    this.loading = false;
    this.posts = [];
    APP_STATE.Posts.offset = 0;
    this.hasMore = true;
    this.selectedPostId = null;
    this.closeArticle();
    this.renderFeed();
    await this.loadPosts();
  }

  async loadPosts() {
    if (this.loading || !this.hasMore) return;
    this.loading = true;
    this.loadMoreButton.disabled = true;
    this.loadMoreButton.textContent = "Carregando...";
    this.listController?.abort();
    const controller = new AbortController();
    this.listController = controller;
    try {
      const query = this.searchTerm ? `&search=${encodeURIComponent(this.searchTerm)}` : "";
      const page = await api.get(`/posts/?limit=${APP_STATE.Posts.limit}&offset=${APP_STATE.Posts.offset}${query}`, { signal: controller.signal });
      this.posts.push(...page);
      APP_STATE.Posts.offset += page.length;
      this.hasMore = page.length === APP_STATE.Posts.limit;
      this.renderFeed();
    } catch (error) {
      if (error.name !== "AbortError") {
        toast(error.message, "error");
        this.feed.replaceChildren();
        const message = document.createElement("p");
        message.className = "sidebar-note";
        message.textContent = "Não foi possível carregar os artigos. Tente atualizar a lista.";
        this.feed.append(message);
      }
    } finally {
      if (this.listController === controller) {
        this.loading = false;
        this.loadMoreButton.disabled = !this.hasMore;
        this.loadMoreButton.textContent = this.hasMore ? "Carregar mais" : "Você chegou ao fim";
      }
    }
  }

  async searchPosts() {
    const version = ++this.searchVersion;
    this.listController?.abort();
    this.posts = []; APP_STATE.Posts.offset = 0; this.hasMore = true; this.selectedPostId = null;
    this.closeArticle(); this.renderFeed();
    const controller = new AbortController(); this.listController = controller; this.loading = true;
    try {
      const query = this.searchTerm ? `&search=${encodeURIComponent(this.searchTerm)}` : "";
      const page = await api.get(`/posts/?limit=${APP_STATE.Posts.limit}&offset=0${query}`, { signal: controller.signal });
      if (version !== this.searchVersion) return;
      this.posts = page; APP_STATE.Posts.offset = page.length; this.hasMore = page.length === APP_STATE.Posts.limit; this.renderFeed();
    } catch (error) { if (error.name !== "AbortError" && version === this.searchVersion) toast(error.message, "error"); }
    finally { if (version === this.searchVersion) { this.loading = false; this.loadMoreButton.disabled = !this.hasMore; this.loadMoreButton.textContent = this.hasMore ? "Carregar mais" : "Você chegou ao fim"; } }
  }

  closeArticle() {
    this.selectedPostId = null;
    this.article.replaceChildren();
    const empty = document.createElement("section"); empty.className = "empty-state";
    const title = document.createElement("h1"); title.textContent = "Conhecimento que move a comunidade.";
    const text = document.createElement("p"); text.textContent = "Selecione um artigo na lista para começar a leitura.";
    empty.append(title, text); this.article.append(empty);
    document.getElementById("comments-section")?.classList.add("hidden");
    document.getElementById("close-article")?.classList.add("hidden");
    document.dispatchEvent(new CustomEvent("talkdev:post-closed"));
    this.renderFeed();
  }

  renderFeed() {
    if (!this.feed) return;
    const filtered = this.posts;
    this.feed.replaceChildren();
    if (!filtered.length) {
      const empty = document.createElement("p");
      empty.className = "sidebar-note";
      empty.textContent = this.searchTerm ? "Nenhum título corresponde à sua pesquisa." : "Ainda não há artigos publicados.";
      this.feed.append(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    filtered.forEach((post) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `feed-card ${post.id === this.selectedPostId ? "active" : ""}`;
      button.dataset.postId = post.id;
      const meta = document.createElement("div");
      meta.className = "feed-meta";
      const author = document.createElement("span");
      author.className = "feed-author";
      author.textContent = `@${post.author?.username || "dev"}`;
      const date = document.createElement("time");
      date.dateTime = post.created_at;
      date.dataset.relativeTime = "true";
      date.textContent = formatDate(post.created_at);
      meta.append(author, document.createTextNode(" · "), date);
      const title = document.createElement("h3");
      title.textContent = post.title;
      const preview = document.createElement("p");
      preview.textContent = post.content;
      button.append(meta, title, preview);
      fragment.append(button);
    });
    this.feed.append(fragment);
  }

  async selectPost(postId) {
    const post = this.posts.find((item) => item.id === postId);
    if (!post) return;
    this.selectedPostId = postId;
    this.renderFeed();
    this.renderArticle(post);
    document.getElementById("close-article")?.classList.remove("hidden");
    document.dispatchEvent(new CustomEvent("talkdev:post-selected", { detail: { post } }));
    if (window.matchMedia("(max-width: 680px)").matches) {
      document.getElementById("feed-sidebar")?.classList.remove("open");
      document.getElementById("mobile-menu-toggle")?.setAttribute("aria-expanded", "false");
    }
  }

  renderArticle(post) {
    this.article.replaceChildren();
    const article = document.createElement("article");
    article.className = "article";
    const header = document.createElement("header");
    header.className = "article-header";
    const title = document.createElement("h1");
    title.className = "article-title";
    title.textContent = post.title;
    const meta = document.createElement("div");
    meta.className = "article-meta";
    const avatar = document.createElement("img");
    avatar.className = "article-avatar";
    avatar.alt = "";
    avatar.loading = "lazy";
    avatar.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(post.author?.username || "dev")}`;
    const authorWrap = document.createElement("div");
    const author = document.createElement("span");
    author.className = "article-author";
    author.textContent = `@${post.author?.username || "dev"}`;
    const date = document.createElement("time");
    date.className = "article-date";
    date.dateTime = post.created_at;
    date.dataset.relativeTime = "true";
    date.textContent = formatDate(post.created_at);
    authorWrap.append(author, date);
    meta.append(avatar, authorWrap);
    if (Session.user?.id === post.author_id) {
      const actions = document.createElement("div");
      actions.className = "article-actions";
      const remove = document.createElement("button");
      remove.className = "button button-quiet";
      remove.type = "button";
      const edit = document.createElement("button");
      edit.className = "button button-quiet";
      edit.type = "button";
      edit.dataset.postAction = "edit";
      edit.textContent = "Editar";
      remove.dataset.postAction = "delete";
      remove.textContent = "Excluir artigo";
      actions.append(edit, remove);
      meta.append(actions);
    }
    header.append(title, meta);

    const body = document.createElement("div");
    body.className = "article-body";
    post.content.split(/\n{2,}/).forEach((paragraphText) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = paragraphText;
      body.append(paragraph);
    });
    article.append(header, body);
    this.article.append(article);
    document.getElementById("comments-section")?.classList.remove("hidden");
  }

  async handlePostAction(action) {
    if (!this.selectedPostId || !Session.token) return;
    if (action === "edit") {
      const post = this.posts.find((item) => item.id === this.selectedPostId);
      if (!post) return;
      this.editingPostId = post.id;
      document.getElementById("post-modal-title").textContent = "Editar artigo";
      document.getElementById("post-title").value = post.title;
      document.getElementById("post-content").value = post.content;
      document.getElementById("post-error").textContent = "";
      this.modal.showModal();
      return;
    }
    if (action !== "delete") return;
    if (!window.confirm("Tem certeza de que deseja excluir este artigo?")) return;
    try {
      await api.delete(`/posts/${this.selectedPostId}`, { token: Session.token });
      this.posts = this.posts.filter((post) => post.id !== this.selectedPostId);
      this.selectedPostId = null;
      this.renderFeed();
      this.article.innerHTML = `
      <section class="empty-state">
        <h1>Artigo excluído.</h1>
        <p>Selecione outro artigo para continuar.</p>
      </section>`;
      
      document.getElementById("comments-section")?.classList.add("hidden");
      toast("Artigo excluído.");
    } catch (error) {
      toast(error.message, "error");
    }
  }

  async createPost(event) {
    event.preventDefault();
    if (!Session.token) {
      window.location.href = "pages/auth.html";
      return;
    }
    const formData = new FormData(this.form);
    const submit = this.form.querySelector('[type="submit"]');
    submit.disabled = true;
    try {
      const payload = {
        title: String(formData.get("title")).trim(),
        content: String(formData.get("content")).trim(),
      };
      const post = this.editingPostId
        ? await api.put(`/posts/${this.editingPostId}`, payload, { token: Session.token })
        : await api.post("/posts/", payload, { token: Session.token });
      if (this.editingPostId) {
        const index = this.posts.findIndex((item) => item.id === this.editingPostId);
        if (index >= 0) this.posts[index] = post;
      } else {
        this.posts.unshift(post);
        APP_STATE.Posts.offset += 1;
      }
      this.editingPostId = null;
      document.getElementById("post-modal-title").textContent = "Novo artigo";
      this.modal.close();
      this.form.reset();
      this.renderFeed();
      await this.selectPost(post.id);
      toast("Artigo salvo com sucesso.");
    } catch (error) {
      document.getElementById("post-error").textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  }
}
