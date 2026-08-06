import { LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import Badge from "@/components/ui/Badge";
import LedgerlineMark from "@/components/ui/LedgerlineMark";

const roleBadgeTone = {
  applicant: "navy",
  staff: "teal",
  admin: "amber",
} as const;

interface AppShellProps {
  children: ReactNode;
}

/**
 * Shared authenticated layout: a top bar with the wordmark, the current
 * user's name/role, and a logout action.
 *
 * Module 1 only has one destination (the dashboard), so there's no side
 * navigation yet — a left sidebar nav will be introduced in a later module
 * once there are actually multiple sections (loans, staff queue, etc.) to
 * navigate between. Building it now would just be an empty list of links.
 */
export default function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-canvas">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5 text-navy">
            <LedgerlineMark className="h-5 w-16" />
            <span className="font-display text-lg font-semibold tracking-tight">Ledgerline</span>
          </Link>

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
