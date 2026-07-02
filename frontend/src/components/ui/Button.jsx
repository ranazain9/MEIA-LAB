import { Link } from "react-router-dom";

export function Button({
  children,
  className = "",
  disabled = false,
  onClick,
  to,
  type = "button",
  variant = "secondary",
}) {
  const classes = `button ${variant} ${className}`.trim();

  if (to) {
    return (
      <Link className={classes} to={to}>
        {children}
      </Link>
    );
  }

  return (
    <button className={classes} disabled={disabled} onClick={onClick} type={type}>
      {children}
    </button>
  );
}
