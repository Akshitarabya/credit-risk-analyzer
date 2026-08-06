import { CalendarClock, Mail, ShieldCheck } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import AppShell from "@/components/layout/AppShell";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";

const roleCopy: Record<string, { headline: string; description: string }> = {
  applicant: {
    headline: "Ready to apply for a loan?",
    description:
      "Once loan applications go live, you'll be able to submit one here and see your risk-scored decision, with a clear explanation of what drove it.",
  },
  staff: {
    headline: "Your review queue will live here.",
    description:
      "Once the scoring pipeline is connected, you'll see every submitted application here, sorted by risk band, ready for review.",
  },
  admin: {
    headline: "Portfolio analytics will live here.",
    description:
      "Once applications start flowing through, this is where you'll track approval rates and portfolio-wide risk distribution.",
  },
};

function formatMemberSince(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });
}

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  const copy = roleCopy[user.role] ?? roleCopy.applicant;

  return (
    <AppShell>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
          Welcome back
        </p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">{user.full_name}</h1>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="font-display text-lg font-semibold text-ink">{copy.headline}</h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted">{copy.description}</p>
          <div className="mt-6 rounded-xl border border-dashed border-line bg-canvas px-4 py-6 text-center">
            <p className="text-sm text-muted">
              This module ships in the next build phase — this is the account
              foundation the rest of the product is built on top of.
            </p>
          </div>
        </Card>

        <Card>
          <h2 className="font-display text-base font-semibold text-ink">Account details</h2>
          <dl className="mt-4 flex flex-col gap-4">
            <div className="flex items-start gap-3">
              <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted">
                  Email
                </dt>
                <dd className="text-sm font-medium text-ink">{user.email}</dd>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted">
                  Account type
                </dt>
                <dd className="mt-0.5">
                  <Badge tone={user.role === "applicant" ? "navy" : "teal"}>{user.role}</Badge>
                </dd>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CalendarClock className="mt-0.5 h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted">
                  Member since
                </dt>
                <dd className="text-sm font-medium text-ink">
                  {formatMemberSince(user.created_at)}
                </dd>
              </div>
            </div>
          </dl>
        </Card>
      </div>
    </AppShell>
  );
}
