import { useEffect, useState, type FormEvent } from "react";
import { AxiosError } from "axios";
import { useNavigate } from "react-router-dom";

import { fetchMyApplicantProfile } from "@/api/applicants";
import { submitLoanApplication } from "@/api/loans";
import AppShell from "@/components/layout/AppShell";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import { getErrorMessage } from "@/utils/errors";
import type { EmploymentStatus } from "@/types/applicant";
import type { LoanPurpose } from "@/types/loan";

const EMPLOYMENT_OPTIONS: { value: EmploymentStatus; label: string }[] = [
  { value: "employed", label: "Employed" },
  { value: "self_employed", label: "Self-employed" },
  { value: "unemployed", label: "Unemployed" },
  { value: "student", label: "Student" },
];

const LOAN_PURPOSE_OPTIONS: { value: LoanPurpose; label: string }[] = [
  { value: "personal", label: "Personal" },
  { value: "auto", label: "Auto" },
  { value: "education", label: "Education" },
  { value: "business", label: "Business" },
  { value: "home", label: "Home" },
];

interface FormState {
  full_name: string;
  date_of_birth: string;
  employment_status: EmploymentStatus;
  annual_income: string;
  existing_debt: string;
  credit_history_years: string;
  loan_amount: string;
  loan_purpose: LoanPurpose;
  loan_tenure_months: string;
}

const EMPTY_FORM: FormState = {
  full_name: "",
  date_of_birth: "",
  employment_status: "employed",
  annual_income: "",
  existing_debt: "0",
  credit_history_years: "0",
  loan_amount: "",
  loan_purpose: "personal",
  loan_tenure_months: "",
};

export default function ApplicationFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [isPrefilling, setIsPrefilling] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If the applicant already has a profile from a previous application,
  // prefill the financial-profile fields so they don't retype everything.
  useEffect(() => {
    fetchMyApplicantProfile()
      .then((profile) => {
        setForm((prev) => ({
          ...prev,
          full_name: profile.full_name,
          date_of_birth: profile.date_of_birth,
          employment_status: profile.employment_status,
          annual_income: String(profile.annual_income),
          existing_debt: String(profile.existing_debt),
          credit_history_years: String(profile.credit_history_years),
        }));
      })
      .catch((err) => {
        // A fresh applicant has no profile yet — that's expected, not an error.
        if (!(err instanceof AxiosError) || err.response?.status !== 404) {
          setError(getErrorMessage(err, "Could not load your saved details."));
        }
      })
      .finally(() => setIsPrefilling(false));
  }, []);

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const application = await submitLoanApplication({
        full_name: form.full_name,
        date_of_birth: form.date_of_birth,
        employment_status: form.employment_status,
        annual_income: Number(form.annual_income),
        existing_debt: Number(form.existing_debt),
        credit_history_years: Number(form.credit_history_years),
        loan_amount: Number(form.loan_amount),
        loan_purpose: form.loan_purpose,
        loan_tenure_months: Number(form.loan_tenure_months),
      });
      navigate(`/applications/${application.id}`, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Could not submit your application. Please check your details."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
          New application
        </p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">Apply for a loan</h1>
        <p className="mt-2 text-sm text-muted">
          Tell us about your finances and what you need — we'll use this to review your
          application.
        </p>

        {isPrefilling ? (
          <Card className="mt-8 flex items-center justify-center py-16">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-line border-t-navy" />
          </Card>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-6">
            {error && <Alert tone="error">{error}</Alert>}

            <Card>
              <h2 className="font-display text-base font-semibold text-ink">
                Your financial profile
              </h2>
              <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Input
                    label="Full legal name"
                    required
                    value={form.full_name}
                    onChange={(e) => updateField("full_name", e.target.value)}
                    placeholder="Jordan Rivera"
                  />
                </div>

                <Input
                  label="Date of birth"
                  type="date"
                  required
                  value={form.date_of_birth}
                  onChange={(e) => updateField("date_of_birth", e.target.value)}
                />

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="employment_status" className="text-sm font-medium text-ink">
                    Employment status
                  </label>
                  <select
                    id="employment_status"
                    required
                    value={form.employment_status}
                    onChange={(e) =>
                      updateField("employment_status", e.target.value as EmploymentStatus)
                    }
                    className="rounded-xl border border-line bg-white px-3.5 py-2.5 text-sm text-ink
                      transition-colors hover:border-navy/30
                      focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
                  >
                    {EMPLOYMENT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Annual income (USD)"
                  type="number"
                  min={1}
                  step="0.01"
                  required
                  value={form.annual_income}
                  onChange={(e) => updateField("annual_income", e.target.value)}
                  placeholder="65000"
                />

                <Input
                  label="Existing debt (USD)"
                  type="number"
                  min={0}
                  step="0.01"
                  required
                  value={form.existing_debt}
                  onChange={(e) => updateField("existing_debt", e.target.value)}
                  placeholder="0"
                />

                <Input
                  label="Credit history (years)"
                  type="number"
                  min={0}
                  max={100}
                  required
                  value={form.credit_history_years}
                  onChange={(e) => updateField("credit_history_years", e.target.value)}
                  placeholder="5"
                  hint="Round down to the nearest year."
                />
              </div>
            </Card>

            <Card>
              <h2 className="font-display text-base font-semibold text-ink">Loan details</h2>
              <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
                <Input
                  label="Loan amount (USD)"
                  type="number"
                  min={1}
                  step="0.01"
                  required
                  value={form.loan_amount}
                  onChange={(e) => updateField("loan_amount", e.target.value)}
                  placeholder="15000"
                />

                <Input
                  label="Tenure (months)"
                  type="number"
                  min={1}
                  max={360}
                  required
                  value={form.loan_tenure_months}
                  onChange={(e) => updateField("loan_tenure_months", e.target.value)}
                  placeholder="48"
                />

                <div className="sm:col-span-2">
                  <label htmlFor="loan_purpose" className="text-sm font-medium text-ink">
                    Purpose
                  </label>
                  <select
                    id="loan_purpose"
                    required
                    value={form.loan_purpose}
                    onChange={(e) => updateField("loan_purpose", e.target.value as LoanPurpose)}
                    className="mt-1.5 w-full rounded-xl border border-line bg-white px-3.5 py-2.5 text-sm text-ink
                      transition-colors hover:border-navy/30
                      focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
                  >
                    {LOAN_PURPOSE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </Card>

            <Button type="submit" isLoading={isSubmitting} className="w-full sm:w-auto sm:self-end">
              Submit application
            </Button>
          </form>
        )}
      </div>
    </AppShell>
  );
}