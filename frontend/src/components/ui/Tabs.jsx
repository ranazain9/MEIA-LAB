export function Tabs({ ariaLabel, items, onChange, value }) {
  return (
    <div className="filter-row" role="tablist" aria-label={ariaLabel}>
      {items.map((item) => (
        <button
          aria-selected={value === item}
          className={value === item ? "active" : ""}
          key={item}
          onClick={() => onChange(item)}
          role="tab"
          type="button"
        >
          {item}
        </button>
      ))}
    </div>
  );
}
