const TOKEN_KEY = "talkdevcode.access_token";
const USER_KEY = "talkdevcode.user";

export class Session {
  static isTokenExpired(token) {
    if (!token) return true;
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      const payload = JSON.parse(jsonPayload);
      
      if (!payload || !payload.exp) return true;

      const currentTimeSeconds = Math.floor(Date.now() / 1000);
      
      return currentTimeSeconds >= payload.exp;
    } catch {
      return true;
    }
  }

  static get token() { 
    const currentToken = sessionStorage.getItem(TOKEN_KEY);
    
    if (currentToken && this.isTokenExpired(currentToken)) {
      this.end();
      return null;
    }
    
    return currentToken; 
  }

  static get user() {
    if (!this.token) return null; 
    
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
