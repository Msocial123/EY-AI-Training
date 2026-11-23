/**
 * TODO BN-701 - Reusable Button
 * Props:
 *   variant   "primary" | "secondary" | "ghost" | "danger"   (default "primary")
 *   size      "sm" | "md" | "lg"                              (default "md")
 *   fullWidth boolean   -> adds class "btn-block"
 *   isLoading boolean   -> shows <span className="spinner" /> and disables the button
 *   children, ...rest   -> rest (onClick, type, disabled, aria-label...) goes onto <button>
 * CSS classes available: btn, btn-primary, btn-secondary, btn-ghost, btn-danger, btn-sm, btn-md, btn-lg, btn-block, spinner
 */
function Button({ children, ...rest }) {
  // TODO: build the className from the props and support isLoading
  return <button className="btn btn-primary btn-md" {...rest}>{children}</button>;
}

export default Button;
