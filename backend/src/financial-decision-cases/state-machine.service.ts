import { Injectable } from '@nestjs/common';
import { ConflictException } from '@nestjs/common';
import { DecisionState } from '@prisma/client';

export const VALID_TRANSITIONS: Record<DecisionState, DecisionState[]> = {
  [DecisionState.DRAFT]: [DecisionState.CLASSIFIED],
  [DecisionState.CLASSIFIED]: [DecisionState.STRUCTURED],
  [DecisionState.STRUCTURED]: [DecisionState.ANALYZED],
  [DecisionState.ANALYZED]: [DecisionState.RECOMMENDED],
  [DecisionState.RECOMMENDED]: [DecisionState.DECIDED],
  [DecisionState.DECIDED]: [DecisionState.UNDER_REVIEW],
  [DecisionState.UNDER_REVIEW]: [DecisionState.CLOSED],
  [DecisionState.CLOSED]: [],
};

@Injectable()
export class StateMachineService {
  isValidTransition(from: DecisionState, to: DecisionState): boolean {
    return VALID_TRANSITIONS[from]?.includes(to) ?? false;
  }

  validateTransition(from: DecisionState, to: DecisionState): void {
    if (!this.isValidTransition(from, to)) {
      throw new ConflictException(
        `Invalid state transition from ${from} to ${to}. Valid transitions from ${from}: [${(VALID_TRANSITIONS[from] || []).join(', ')}]`,
      );
    }
  }
}
