import { IsString, IsNotEmpty, IsEnum } from 'class-validator';
import { FinancialDomain, DecisionType } from '@prisma/client';

export class ClassifyCaseDto {
  @IsEnum(FinancialDomain)
  financialDomain: FinancialDomain;

  @IsEnum(DecisionType)
  decisionType: DecisionType;

  @IsString()
  @IsNotEmpty()
  classificationRationale: string;
}
