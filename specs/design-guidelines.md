# Design Guidelines

## Layout
One page with two views under a slim header. The entry view is compact: a biomarker form beside a dedicated educational-chatbot panel. After a successful prediction, hide the form and show a results dashboard with a probability gauge, factor bars, submitted-value table, and the same dedicated chatbot panel. The chat panel remains open in the side column; it is never a modal. Below 900 px the columns stack. It must not receive form values, prediction output, or result text.

## Entry view
1. Heading + short patient-facing subtitle
2. Compact form, preserving raw-input order: `pT217_F`, `AB42_AB40_F`, `GFAP_Q`, `APOE4`, `AGE`, `SEX`. The backend, not the user, derives the two ratio features required by the model.
3. Show only confirmed observed numeric ranges immediately below each field; do not invent units or clinical ranges.
4. Buttons: Predict (primary) and Reset (secondary). The independent educational chatbot remains visible in the adjacent panel.
5. Disclaimer: "Screening aid, not a diagnosis."

## Results view
1. Summary heading and "Start a new screening" action.
2. Semicircular probability gauge with text category, percentage, and one-sentence explanation.
3. Top-factor bars.
4. Submitted-value table, labelled as values used only for the current prediction and not stored.
5. The dedicated educational-chatbot panel stays visually adjacent only; it must not imply that the chatbot can explain the user's result.

## Educational chatbot
1. Heading "Learn about preclinical Alzheimer's" + subtitle.
2. Show a dedicated side panel with a scrollable message area, welcome message, starter-question chips, compact textarea, Send button, typing state, and footer disclaimer. Answers from the loaded literature show source chips; general Gemini fallback answers show a small provenance note beneath the message stating that they are not from the loaded literature.
3. The handler posts only `{message, history}` to `/api/chat`; it never reads the form, prediction banner, factor bars, or prediction response.

## Colours
Page #F4F6F8 · Card #FFF, border #DDE3E9 · Text #14202B / #44525F · Brand #0F6E7A
Low #2F7D4F on #E3F1E8 · Moderate #8A6A00 on #FFF3C9 · Elevated #C2570C on #FDE8D3 (orange, not red)

## Type and components
Inter (fallback system-ui). Heading 18 px/600, body 14 px, result number 40 px/600. Cards 12 px radius, 20 px padding. Inputs and buttons min height 44 px. User chat bubbles teal, assistant bubbles light grey. Plain CSS with variables on `:root`; no framework.

## States
Empty result, loading (button shows "Predicting..."), field error, server error banner, chat typing indicator, "couldn't find" reply.

## Accessibility
Real `<label>` for every input, `aria-live="polite"` on the result banner and chat log, visible focus rings, text label with every colour.
