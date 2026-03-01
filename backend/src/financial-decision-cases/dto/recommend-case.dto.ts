import { IsOptional, IsString } from 'class-validator';

export class RecommendCaseDto {
  @IsString()
  @IsOptional()
  additionalContext?: string;
}
