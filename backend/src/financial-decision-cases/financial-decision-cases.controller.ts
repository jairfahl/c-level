import {
  Controller,
  Get,
  Post,
  Put,
  Body,
  Param,
  UseGuards,
  Request,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { FinancialDecisionCasesService } from './financial-decision-cases.service';
import { CreateCaseDto } from './dto/create-case.dto';
import { ClassifyCaseDto } from './dto/classify-case.dto';
import { StructureCaseDto } from './dto/structure-case.dto';
import { AnalyzeCaseDto } from './dto/analyze-case.dto';
import { RecommendCaseDto } from './dto/recommend-case.dto';
import { DecideCaseDto } from './dto/decide-case.dto';
import { ReviewCaseDto } from './dto/review-case.dto';

@UseGuards(JwtAuthGuard)
@Controller('financial-decision-cases')
export class FinancialDecisionCasesController {
  constructor(private readonly service: FinancialDecisionCasesService) {}

  @Post()
  create(@Body() dto: CreateCaseDto, @Request() req) {
    return this.service.create(dto, req.user.id);
  }

  @Get()
  findAll() {
    return this.service.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.service.findOne(id);
  }

  @Put(':id/classify')
  classify(@Param('id') id: string, @Body() dto: ClassifyCaseDto, @Request() req) {
    return this.service.classify(id, dto, req.user.id);
  }

  @Put(':id/structure')
  structure(@Param('id') id: string, @Body() dto: StructureCaseDto, @Request() req) {
    return this.service.structure(id, dto, req.user.id);
  }

  @Put(':id/analyze')
  analyze(@Param('id') id: string, @Body() dto: AnalyzeCaseDto, @Request() req) {
    return this.service.analyze(id, dto, req.user.id);
  }

  @Put(':id/recommend')
  recommend(@Param('id') id: string, @Body() dto: RecommendCaseDto, @Request() req) {
    return this.service.recommend(id, dto, req.user.id);
  }

  @Put(':id/decide')
  decide(@Param('id') id: string, @Body() dto: DecideCaseDto, @Request() req) {
    return this.service.decide(id, dto, req.user.id);
  }

  @Put(':id/review')
  review(@Param('id') id: string, @Body() dto: ReviewCaseDto, @Request() req) {
    return this.service.review(id, dto, req.user.id);
  }
}
