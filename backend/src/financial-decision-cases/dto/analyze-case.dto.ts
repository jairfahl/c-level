import {
  IsArray,
  IsString,
  IsNotEmpty,
  IsNumber,
  IsInt,
  IsOptional,
  ValidateNested,
  Min,
  Max,
} from 'class-validator';
import { Type } from 'class-transformer';

export class MetricImpactedDto {
  @IsString()
  @IsNotEmpty()
  metricName: string;

  @IsNumber()
  currentValue: number;

  @IsNumber()
  projectedValue: number;

  @IsString()
  @IsNotEmpty()
  unit: string;

  @IsInt()
  @Min(1)
  timeHorizonMonths: number;
}

export class AnalyzeCaseDto {
  @IsArray()
  @IsOptional()
  @ValidateNested({ each: true })
  @Type(() => MetricImpactedDto)
  metricsImpacted?: MetricImpactedDto[];

  @IsString()
  @IsOptional()
  scenarioNotes?: string;
}
