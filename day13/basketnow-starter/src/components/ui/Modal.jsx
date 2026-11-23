/**
 * TODO BN-701 - Modal dialog
 * Props: isOpen, title, onClose, children, footer
 * - return null when !isOpen
 * - clicking the dark backdrop calls onClose; clicks inside the box must NOT (stopPropagation)
 * - pressing Escape calls onClose: add a keydown listener in useEffect, remove it in the cleanup
 * CSS: overlay, modal, modal-head, modal-body, modal-foot, icon-btn
 */
function Modal({ isOpen }) {
  if (!isOpen) return null;
  return null; // TODO
}

export default Modal;
