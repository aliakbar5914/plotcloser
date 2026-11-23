// Who is this visitor? No login for customers: we give each browser a random id.
// localStorage keeps it after the tab closes, so long-term memory recognises them next time.

const USER_KEY = "plotcloser_user_id";
const THREAD_KEY = "plotcloser_thread_id";

export function getUserId(): string {
  let userId = localStorage.getItem(USER_KEY);
  if (!userId) {
    userId = `web_${crypto.randomUUID()}`;
    localStorage.setItem(USER_KEY, userId);
  }
  return userId;
}

export function getThreadId(): string {
  let threadId = localStorage.getItem(THREAD_KEY);
  if (!threadId) threadId = startNewThread();
  return threadId;
}

// "New chat" = new thread_id = empty short-term memory (long-term memory stays).
export function startNewThread(): string {
  const threadId = `chat_${crypto.randomUUID()}`;
  localStorage.setItem(THREAD_KEY, threadId);
  return threadId;
}
