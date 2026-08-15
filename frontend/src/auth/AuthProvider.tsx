import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";
import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import { setAccessTokenGetter } from "@/api/axiosInstance";

export type Role = "Admin" | "Manager" | "Viewer";

type AuthShape = {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: { name?: string; email?: string; picture?: string } | null;
  role: Role;
  setRole: (r: Role) => void;
  login: () => void;
  logout: () => void;
  authMode: "auth0" | "mock";
};

const AuthCtx = createContext<AuthShape | null>(null);
export const useAuth = () => {
  const v = useContext(AuthCtx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
};

const DOMAIN     = import.meta.env.VITE_AUTH0_DOMAIN as string | undefined;
const CLIENT_ID  = import.meta.env.VITE_AUTH0_CLIENT_ID as string | undefined;
const AUDIENCE   = import.meta.env.VITE_AUTH0_AUDIENCE as string | undefined;
const ROLES_CLAIM = (import.meta.env.VITE_AUTH0_ROLES_CLAIM as string) || "https://smartevm/roles";

const Auth0Bridge = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading, user, loginWithRedirect, logout, getAccessTokenSilently, getIdTokenClaims } = useAuth0();
  const [role, setRole] = useState<Role>("Viewer");

  useEffect(() => {
    setAccessTokenGetter(async () => {
      try {
        if (!isAuthenticated) return null;
        return await getAccessTokenSilently({ authorizationParams: AUDIENCE ? { audience: AUDIENCE } : undefined });
      } catch { return null; }
    });
  }, [isAuthenticated, getAccessTokenSilently]);

  useEffect(() => {
    (async () => {
      if (!isAuthenticated) return;
      try {
        const claims: any = await getIdTokenClaims();
        const roles: string[] = (claims && claims[ROLES_CLAIM]) || (user && (user as any)[ROLES_CLAIM]) || [];
        const r = roles.find((x) => ["Admin", "Manager", "Viewer"].includes(x)) as Role | undefined;
        setRole(r ?? "Viewer");
      } catch { setRole("Viewer"); }
    })();
  }, [isAuthenticated, user, getIdTokenClaims]);

  const value: AuthShape = {
    isAuthenticated, isLoading,
    user: user ? { name: user.name, email: user.email, picture: user.picture } : null,
    role, setRole,
    login: () => loginWithRedirect(),
    logout: () => logout({ logoutParams: { returnTo: window.location.origin } }),
    authMode: "auth0",
  };
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
};

const MockBridge = ({ children }: { children: ReactNode }) => {
  const [role, setRole] = useState<Role>(() => (localStorage.getItem("smartevm.role") as Role) || "Admin");
  useEffect(() => { localStorage.setItem("smartevm.role", role); }, [role]);
  useEffect(() => { setAccessTokenGetter(async () => null); }, []);
  const value: AuthShape = useMemo(() => ({
    isAuthenticated: true, isLoading: false,
    user: { name: "Demo User", email: "demo@smartevm.io" },
    role, setRole,
    login: () => {}, logout: () => {},
    authMode: "mock",
  }), [role]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  if (DOMAIN && CLIENT_ID) {
    return (
      <Auth0Provider
        domain={DOMAIN}
        clientId={CLIENT_ID}
        authorizationParams={{
          redirect_uri: window.location.origin,
          ...(AUDIENCE ? { audience: AUDIENCE } : {}),
        }}
        cacheLocation="localstorage"
      >
        <Auth0Bridge>{children}</Auth0Bridge>
      </Auth0Provider>
    );
  }
  return <MockBridge>{children}</MockBridge>;
};

export const RoleGate = ({ allow, children, fallback = null }: {
  allow: Role[]; children: ReactNode; fallback?: ReactNode;
}) => {
  const { role } = useAuth();
  return allow.includes(role) ? <>{children}</> : <>{fallback}</>;
};
