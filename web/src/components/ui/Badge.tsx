import { cn } from "@/lib/cn";

type BadgeVariant = "accent" | "green" | "red" | "yellow" | "purple" | "muted";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  accent: "bg-accent/15 text-cyan-400",
  green: "bg-emerald-500/12 text-emerald-400",
  red: "bg-red-500/12 text-red-400",
  yellow: "bg-amber-500/12 text-amber-400",
  purple: "bg-violet-500/12 text-violet-400",
  muted: "bg-gray-700/50 text-gray-400",
};

export function Badge({ variant = "muted", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}