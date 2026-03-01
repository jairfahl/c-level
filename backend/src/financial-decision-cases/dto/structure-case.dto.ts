import {
  IsArray,
  IsString,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  ValidateNested,
  Min,
  Max,
  ArrayMinSize,
} from 'class-validator';
import { Type } from 'class-transformer';

export class AssumptionDto {
  @IsString()
  @IsNotEmpty()
  description: string;

  @IsString()
  @IsNotEmpty()
  source: string;

  @IsNumber()
  @Min(0)
  @Max(1)
  confidence: number;
}

export class RiskDto {
  @IsString()
  @IsNotEmpty()
  description: string;

  @IsNumber()
  @Min(0)
  @Max(1)
  probability: number;

  @IsNumber()
  @Min(1)
  @Max(5)
  impactScore: number;

  @IsString()
  @IsOptional()
  mitigationPlan?: string;

  @IsNumber()
  @IsOptional()
  @Min(0)
  @Max(1)
  residualRisk?: number;
}

export class StructureCaseDto {
  @IsArray()
  @ArrayMinSize(3)
  @ValidateNested({ each: true })
  @Type(() => AssumptionDto)
  assumptions: AssumptionDto[];

  @IsArray()
  @ArrayMinSize(1)
  @ValidateNested({ each: true })
  @Type(() => RiskDto)
  risks: RiskDto[];
}
