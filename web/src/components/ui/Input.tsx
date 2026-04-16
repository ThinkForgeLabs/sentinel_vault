import React from "react";
import { cn } from "@/lib/cn";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, className, ...props }, ref) => (
    <div className="w-full">
      {label && (
        <label className="block text-xs font-semibold text-gray-400 mb-1.5">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={cn(
          "w-full rounded-lg border bg-elevated px-3.5 py-2.5 text-sm text-white placeholder-gray-500 outline-none transition-colors focus:border-accent",
          error ? "border-red-500" : "border-border",
          className
        )}
        {...props}
      />
      {hint && !error && (
        <p className="mt-1 text-xs text-gray-500">{hint}</p>
      )}
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
);

Input.displayName = "Input";