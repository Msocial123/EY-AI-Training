/**
 * TODO BN-402 - OptionCards: radio-button group rendered as cards (used for slots AND payment)
 * Props: name, options [{ id, label, detail, meta }], value, onChange(id), disabledIds { [id]: "reason" }
 * - each card is a <label> containing <input type="radio">
 * - selected card gets class "selected"; disabled card gets "disabled" and shows the reason instead of detail
 * CSS: option-cards, option-card, selected, disabled, option-text, option-meta
 */
function OptionCards({ name }) {
  return <div className="todo"><b>BN-402</b> OptionCards ({name})</div>;
}

export default OptionCards;
