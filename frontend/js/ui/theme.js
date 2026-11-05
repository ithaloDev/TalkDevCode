const THEME_KEY = "talkdevcode.theme";

export class ThemeController {
  constructor(button) {
    this.button = button;
    this.theme = localStorage.getItem(THEME_KEY)
      || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    this.apply();
    this.button?.addEventListener("click", () => this.toggle());
  }

  apply() {
    document.documentElement.dataset.theme = this.theme;
    if (this.button) {
      this.button.textContent = this.theme === "dark" ? "☀" : "☾";
      this.button.setAttribute("aria-label", this.theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro");
      this.button.title = this.theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro";
    }
    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) themeColor.content = this.theme === "dark" ? "#070B14" : "#F4F7F4";
  }

  toggle() {
    this.theme = this.theme === "dark" ? "light" : "dark";
    localStorage.setItem(THEME_KEY, this.theme);
    this.apply();
  }
}
