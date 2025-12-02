// Allowed email domains for sign-in
// Add domains without the @ symbol
export const ALLOWED_DOMAINS = [
  'fractile.ai',
  // add more domains as needed
];

export const ALLOWED_EMAILS = [
  'sylvain.viguier@gmail.com',
  // add more emails as needed
];

// Helper function to check if email domain is allowed
export function isEmailAllowed(email: string): boolean {
  const domain = email.split('@')[1]?.toLowerCase();
  return ALLOWED_EMAILS.includes(email.toLowerCase()) || ALLOWED_DOMAINS.includes(domain);
}
