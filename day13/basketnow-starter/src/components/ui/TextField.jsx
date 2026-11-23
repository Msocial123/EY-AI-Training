/**
 * TODO BN-701 - TextField: label + input + error/hint
 * Props: label, name, error, hint, ...inputProps (value, onChange, onBlur, type, maxLength...)
 * - id must be `field-${name}` and the <label htmlFor> must match it
 * - aria-invalid={Boolean(error)}
 * - show error in <p className="field-error">, otherwise hint in <p className="field-hint">
 * CSS: field, has-error, field-error, field-hint
 */
function TextField({ label, name, ...inputProps }) {
  return (
    <div className="field">
      <label htmlFor={`field-${name}`}>{label}</label>
      <input id={`field-${name}`} name={name} {...inputProps} />
    </div>
  );
}

export default TextField;
