import type { ReactNode } from "react";

interface ChartFrameProps {
  title: string;
  description?: string;
  footer?: string;
  children: ReactNode;
}

export function ChartFrame({ title, description, footer, children }: ChartFrameProps) {
  return (
    <section className="chart-frame" aria-label={title}>
      <header className="chart-frame__header">
        <div>
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </div>
        <span className="chart-frame__tag">VISUALIZATION</span>
      </header>
      <div className="chart-frame__body">{children}</div>
      {footer && <footer className="chart-frame__footer">{footer}</footer>}
    </section>
  );
}
