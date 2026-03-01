import { IsString, IsNotEmpty, IsOptional } from 'class-validator';

export class DecideCaseDto {
  @IsString()
  @IsNotEmpty()
  executiveDecision: string;

  @IsString()
  @IsOptional()
  divergenceJustification?: string;
}
