import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      username: string;
      email: string;
      isAdmin: boolean;
      is2faVerified: boolean;
    };
  }

  interface User {
    id: string;
    name: string;
    email: string;
    isAdmin: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    username: string;
    isAdmin: boolean;
    is2faVerified: boolean;
  }
}
