import { createActionClient, ActionClientOptions, createActionMeta } from './actions';

export function createActions(options: ActionClientOptions = {}) {
  const call = createActionClient({
    ...options,
    meta: options.meta ?? (() => createActionMeta()),
  });
  return {
    actions: {},
    call,
  };
}
