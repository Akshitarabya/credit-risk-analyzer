import { type TextareaHTMLAttributes, forwardRef, useId } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, id, className = "", ...rest }, ref) => {
    const generatedId = useId();
    const textareaId = id ?? generatedId;
    const errorId = `${textareaId}-error`;
    const hintId = `${textareaId}-hint`;

    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={textareaId} className="text-sm font-medium text-ink">
          {label}
        </label>
        <textarea
          ref={ref}
          id={textareaId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={`rounded-xl border bg-white px-3.5 py-2.5 text-sm text-ink placeholder:text-muted/70
            transition-colors duration-150 focus-visible:outline focus-visible:outline-2
            focus-visible:outline-offset-2 focus-visible:outline-navy disabled:cursor-not-allowed disabled:bg-canvas disabled:text-muted
            ${error ? "border-coral" : "border-line hover:border-navy/30"} ${className}`}
          {...rest}
        />
        {error ? (
          <p id={errorId} className="text-xs font-medium text-coral">
            {error}
          </p>
        ) : hint ? (
          <p id={hintId} className="text-xs text-muted">
            {hint}
          </p>
        ) : null}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export default Textarea;