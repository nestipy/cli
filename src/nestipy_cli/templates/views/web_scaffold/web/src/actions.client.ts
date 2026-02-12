import { createActionClient, ActionClientOptions } from './actions';

export function createActions(options: ActionClientOptions = {}) {
  const call = createActionClient(options);
  return {
    AppActions: {
      hello: (params: { name?: string } = {}) =>
        call<string>('AppActions.hello', [], params),
    },
    call,
  };
}
