import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import AuthLayout from "@/components/layout/AuthLayout";
import { getErrorMessage } from "@/utils/errors";
import type { UserRole } from "@/types/auth";

const ACCOUNT_TYPES: { value: UserRole; label: string; description: string }[] = [
  { value: "applicant", label: "Applicant", description: "I'm applying for a loan" },
  { value: "staff", label: "Bank staff", description: "I review applications" },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState<UserRole>("applicant");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({ full_name: fullName, email, password, role });
      navigate("/", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Could not create your account."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="Get started"
      title="Built for both sides of the desk."
      subtitle="Applicants get a clear, fast decision. Staff get a scored queue with the reasoning behind every score, so review is fast and defensible."
    >
      <h2 className="font-display text-2xl font-semibold text-ink">Create your account</h2>
      <p className="mt-1.5 text-sm text-muted">It only takes a minute.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        {error && <Alert tone="error">{error}</Alert>}

        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink">I am a</span>
          <div className="grid grid-cols-2 gap-2">
            {ACCOUNT_TYPES.map((option) => {
              const isSelected = role === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setRole(option.value)}
                  aria-pressed={isSelected}
                  className={`rounded-xl border px-3.5 py-2.5 text-left transition-colors
                    focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy
                    ${isSelected ? "border-navy bg-navy/5" : "border-line hover:border-navy/30"}`}
                >
                  <span className="block text-sm font-semibold text-ink">{option.label}</span>
                  <span className="block text-xs text-muted">{option.description}</span>
                </button>
              );
            })}
          </div>
        </div>

        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Jordan Rivera"
        />

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
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          hint="Minimum 8 characters."
        />

        <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
          Create account
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-navy hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
