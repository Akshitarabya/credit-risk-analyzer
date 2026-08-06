import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import AuthLayout from "@/components/layout/AuthLayout";
import { getErrorMessage } from "@/utils/errors";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? "/";

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Incorrect email or password."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="Loan decisioning platform"
      title="Every decision, explained clearly."
      subtitle="Ledgerline scores loan applications with a trained risk model, shows exactly which factors mattered, and turns that into a plain-English explanation for every applicant."
    >
      <h2 className="font-display text-2xl font-semibold text-ink">Welcome back</h2>
      <p className="mt-1.5 text-sm text-muted">Log in to your Ledgerline account.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        {error && <Alert tone="error">{error}</Alert>}

        <Input
          label="Email address"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />

        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />

        <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
          Log in
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted">
        Don't have an account?{" "}
        <Link to="/register" className="font-semibold text-navy hover:underline">
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}
