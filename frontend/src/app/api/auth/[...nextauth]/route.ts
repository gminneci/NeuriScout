import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { isEmailAllowed } from "@/config/allowedDomains"

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Email',
      credentials: {
        email: { label: "Email", type: "email", placeholder: "your@email.com" }
      },
      async authorize(credentials) {
        // Simple email-only authentication with domain restriction
        if (credentials?.email && isEmailAllowed(credentials.email)) {
          return {
            id: credentials.email,
            email: credentials.email,
            name: credentials.email.split('@')[0],
          }
        }
        return null
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      // Add user ID to session
      if (session.user) {
        session.user.id = token.sub!;
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
  },
})

export { handler as GET, handler as POST }
