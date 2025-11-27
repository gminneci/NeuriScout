// Allowed email domains for sign-in
// Add domains without the @ symbol
export const ALLOWED_DOMAINS = [
  'fractile.ai',
];

// Helper function to check if email domain is allowed
export function isEmailAllowed(email: string): boolean {
  const domain = email.split('@')[1]?.toLowerCase();
  return ALLOWED_DOMAINS.includes(domain);
}
