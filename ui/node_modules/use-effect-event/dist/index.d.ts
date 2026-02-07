/**
* This is a ponyfill of the upcoming `useEffectEvent` hook that'll arrive in React 19.
* https://19.react.dev/learn/separating-events-from-effects#declaring-an-effect-event
* To learn more about the ponyfill itself, see: https://blog.bitsrc.io/a-look-inside-the-useevent-polyfill-from-the-new-react-docs-d1c4739e8072
* @public
*/
declare function useEffectEvent<const T extends (...args: any[]) => void>(fn: T): T;
export { useEffectEvent };