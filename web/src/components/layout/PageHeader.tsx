interface PageHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 className="text-xl font-bold">{title}</h2>
        {description && (
          <p className="mt-0.5 text-sm text-gray-400">{description}</p>
        )}
      </div>
      {action && <div className="mt-3 sm:mt-0">{action}</div>}
    </div>
  );
}