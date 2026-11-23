/**
 * TODO BN-701 - EmptyState (empty cart, no search results, no orders, load errors)
 * Props: icon (emoji), title, message, action (any JSX, e.g. a Button), tone "neutral" | "error"
 * CSS: empty-state, empty-<tone>, empty-icon
 */
function EmptyState({ title }) {
  return <div className="empty-state"><h3>{title}</h3></div>;
}

export default EmptyState;
