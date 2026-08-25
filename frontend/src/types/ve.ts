/**
 * Value Engineering — strict TypeScript mirror of the Pydantic models in
 * `app/parsers/value_engineering_engine.py` (VEOpportunityCard / VESummary).
 */

export type SbcStatus = 'COMPLIANT' | 'BLOCKED';

export interface VEOpportunityCard {
  boq_item: string;
  original_spec: string;
  proposed_alternative: string;
  unit_delta_sar: number;
  net_savings_sar: number;
  speed_index_gain_percent: number;
  sbc_status: SbcStatus;
  is_recommended: boolean;
  technical_justification: string;
  sbc_304_references: string[];
  is_accepted: boolean;
}

export interface VESummary {
  total_potential_savings_sar: number;
  net_schedule_acceleration_percent: number;
  total_sbc_verified_proposals: number;
  total_blocked: number;
}