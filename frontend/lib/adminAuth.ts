// The admin password is kept only in sessionStorage (cleared when the tab closes)
// and sent to the API in the X-Admin-Password header. It is never in the website code.

const KEY = "plotcloser_admin_password";

export function getAdminPassword(): string | null {
  return sessionStorage.getItem(KEY);
}

export function saveAdminPassword(password: string): void {
  sessionStorage.setItem(KEY, password);
}

export function clearAdminPassword(): void {
  sessionStorage.removeItem(KEY);
}
