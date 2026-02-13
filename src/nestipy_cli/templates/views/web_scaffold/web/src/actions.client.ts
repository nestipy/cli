import { createActionClient, ActionClientOptions, createActionMetaProvider, ActionResponse } from './actions';

export type AppActionsHelloPayload = {
  name?: string;
};

export function createActions(options: ActionClientOptions = {}) {
  const call = createActionClient({
    ...options,
    meta: options.meta ?? createActionMetaProvider(),
  });
  const AppActions = {
    hello: (payload: AppActionsHelloPayload = {}): Promise<ActionResponse<string>> =>
      call<string>('AppActions.hello', [], payload),
  };
  return {
    actions: { AppActions },
    AppActions,
    call,
  };
}
