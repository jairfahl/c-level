import {
  IsString,
  IsNotEmpty,
  IsEnum,
  IsInt,
  IsBoolean,
  IsOptional,
  Min,
  Max,
} from 'class-validator';
import { FinancialDomain, DecisionType } from '@prisma/client';

export class CreateCaseDto {
  @IsString()
  @IsNotEmpty()
  title: string;

  @IsString()
  @IsNotEmpty()
  description: string;

  @IsEnum(FinancialDomain)
  financialDomain: FinancialDomain;

  @IsEnum(DecisionType)
  decisionType: DecisionType;

  @IsInt()
  @Min(1)
  @Max(5)
  impactScore: number;

  @IsBoolean()
  @IsOptional()
  externalAgentsPresent?: boolean;

  @IsBoolean()
  @IsOptional()
  scenarioAnalysisRequired?: boolean;
}
