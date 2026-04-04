/**
 * Protocol exports
 */

export {
  PROTOCOL_VERSION,
  MessageType,
  NodeStatus,
  Phase,
} from './messageTypes';

export type {
  BlueclawMessage,
  ThinkingOptionData,
  NodeMetadata,
  BlueprintNodeData,
  ThinkingNodeData,
  ExecutionStepData,
  InterventionActionData,
  EngineStateData,
  TaskStartPayload,
  SelectOptionPayload,
  CustomInputPayload,
  ConfirmExecutionPayload,
  IntervenePayload,
  ExecutionStepStartedPayload,
  ExecutionStepCompletedPayload,
  ExecutionStepFailedPayload,
  ExecutionInterventionNeededPayload,
  ExecutionCompletedPayload,
  ExecutionReplannedPayload,
  ErrorPayload,
  ConnectedPayload,
  VersionCompatibility,
} from './messageTypes';

export { MessageFactory, checkVersionCompatibility, parseMessage, stringifyMessage } from './messageTypes';
