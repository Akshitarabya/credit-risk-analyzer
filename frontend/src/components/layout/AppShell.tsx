import { LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import Badge from "@/components/ui/Badge";
import LedgerlineMark from "@/components/ui/LedgerlineMark";

const roleBadgeTone = {
  applicant: "navy",
  staff: "teal",
  admin: "amber",
} as const;

const NAV_ITEMS_BY_ROLE: Record<string, { to: string; label: string }[]> = {
  applicant: [
    { to: "/", label: "Dashboard" },
    { to: "/applications", label: "My applications" },
  ],
  staff: [
    { to: "/", label: "Dashboard" },
    { to: "/staff/applications", label: "Application queue" },
  ],
  admin: [
    { to: "/", label: "Dashboard" },
    { to: "/staff/applications", label: "Application queue" },
  ],
};

interface AppShellProps {
  children: ReactNode;
}

/**
 * Shared authenticated layout: a top bar with the wordmark, role-aware
 * navigation, the current user's name/role, and a logout action.
 */
export default function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navItems = user ? NAV_ITEMS_BY_ROLE[user.role] ?? [] : [];

  return (
    <div className="min-h-screen bg-canvas">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2.5 text-navy">
              <LedgerlineMark className="h-5 w-16" />
              <span className="font-display text-lg font-semibold tracking-tight">
                Ledgerline
              </span>
            </Link>

            {navItems.length > 0 && (
              <nav className="hidden items-center gap-1 sm:flex">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.to;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors
                        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy
                        ${isActive ? "bg-navy/5 text-navy" : "text-muted hover:bg-navy/5 hover:text-navy"}`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            )}
          </div>

          {user && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2.5">
                <div className="text-right">
                  <p className="text-sm font-semibold leading-tight text-ink">{user.full_name}</p>
                  <p className="text-xs leading-tight text-muted">{user.email}</p>
                </div>
                <Badge tone={roleBadgeTone[user.role]}>{user.role}</Badge>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-muted
                  transition-colors hover:bg-navy/5 hover:text-navy
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Log out
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
