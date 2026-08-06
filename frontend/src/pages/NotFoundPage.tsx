import { Link } from "react-router-dom";

import Button from "@/components/ui/Button";
import LedgerlineMark from "@/components/ui/LedgerlineMark";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-canvas px-6 text-center">
      <LedgerlineMark className="h-6 w-20 text-navy/40" />
      <h1 className="font-display text-4xl font-semibold text-ink">Page not found</h1>
      <p className="max-w-sm text-sm text-muted">
        The page you're looking for doesn't exist or may have moved.
      </p>
      <Link to="/">
        <Button variant="secondary" className="mt-2">
          Back to dashboard
        </Button>
      </Link>
    </div>
  );
}
