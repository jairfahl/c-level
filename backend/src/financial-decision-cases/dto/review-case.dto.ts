import { IsString, IsNotEmpty, IsDateString } from 'class-validator';

export class ReviewCaseDto {
  @IsString()
  @IsNotEmpty()
  actualOutcome: string;

  @IsString()
  @IsNotEmpty()
  varianceAnalysis: string;

  @IsString()
  @IsNotEmpty()
  lessonsLearned: string;

  @IsDateString()
  reviewedAt: string;
}
