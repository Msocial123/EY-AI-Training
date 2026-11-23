/**
 * TODO BN-701 - Badge
 * Props: tone "green" | "yellow" | "red" | "blue" | "grey" (default "grey"), children
 * CSS: badge, badge-<tone>
 */
function Badge({ children }) {
  return <span className="badge badge-grey">{children}</span>;
}

export default Badge;
