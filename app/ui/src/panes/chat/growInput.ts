/**
 * Chat input height: one line when empty, grows with the text up to the
 * CSS max-height (css/panes/chat/agent-chat.css), then scrolls.
 *
 * Done here rather than with CSS `field-sizing: content`, which Safari
 * does not support. Code that sets the value itself (Send clears it, the
 * / menu fills it) dispatches an "input" event, so listening to "input"
 * covers those too.
 */

export function installInputGrow(input: HTMLTextAreaElement): void {
  const fit = (): void => {
    // Measure from zero so scrollHeight is the text's own height, not
    // the rows="2" default or the previous, taller height.
    input.style.height = "0px";
    const border = input.offsetHeight - input.clientHeight;
    const max = parseFloat(getComputedStyle(input).maxHeight);
    const wanted = input.scrollHeight + border;
    input.style.height = `${Number.isFinite(max) ? Math.min(wanted, max) : wanted}px`;
  };

  input.addEventListener("input", fit);
  // A narrower or wider chat column rewraps the text. Only width counts:
  // fit() itself changes the height, which must not trigger another fit.
  let lastWidth = input.clientWidth;
  new ResizeObserver(() => {
    if (input.clientWidth === lastWidth) return;
    lastWidth = input.clientWidth;
    fit();
  }).observe(input);
  fit();
}
