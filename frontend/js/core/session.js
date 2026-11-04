const TOKEN_KEY = "talkdevcode.access_token";
const USER_KEY = "talkdevcode.user";

export class Session {
  static get token() { return sessionStorage.getItem(TOKEN_KEY); }
  static get user() {
    try { return JSON.parse(sessionStorage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  }
  static get isAuthenticated() { return Boolean(this.token && this.user); }

  static start(token, user) {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  static end() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  }
}
